from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from dlp.db.session import session_scope
from dlp.domains.jobs.models import Job
from dlp.domains.jobs.service import backoff_delay, claim_next, drain, enqueue, process_one


def test_enqueue_is_idempotent(database):
    with session_scope() as session:
        first = enqueue(session, "echo", {"n": 1}, idempotency_key="echo-1")
        again = enqueue(session, "echo", {"n": 2}, idempotency_key="echo-1")
        assert first.id == again.id
        assert again.payload == {"n": 1}


def test_jobs_run_to_completion(database, settings):
    with session_scope() as session:
        enqueue(session, "echo", {"hello": "world"}, idempotency_key="echo-run")
    assert drain(settings, worker_id="t1") == 1
    with session_scope() as session:
        job = session.scalar(select(Job).where(Job.idempotency_key == "echo-run"))
        assert job.status == "done"
        assert job.result == {"echo": {"hello": "world", "_attempt": 1}}
        assert job.attempts == 1 and job.lease_owner == ""


def test_failed_jobs_retry_with_backoff_then_succeed(database, settings):
    with session_scope() as session:
        enqueue(session, "fail_then_succeed", {"succeed_on": 3}, idempotency_key="flaky", max_attempts=5)
    assert process_one(settings, "t1") is True
    with session_scope() as session:
        job = session.scalar(select(Job).where(Job.idempotency_key == "flaky"))
        assert job.status == "queued" and job.attempts == 1
        assert "injected failure" in job.last_error
        assert job.run_after > datetime.now(UTC) - timedelta(seconds=1)
        job.run_after = datetime.now(UTC)  # skip the wait in tests
    assert process_one(settings, "t1") is True
    with session_scope() as session:
        job = session.scalar(select(Job).where(Job.idempotency_key == "flaky"))
        assert job.status == "queued" and job.attempts == 2
        job.run_after = datetime.now(UTC)
    assert process_one(settings, "t1") is True
    with session_scope() as session:
        job = session.scalar(select(Job).where(Job.idempotency_key == "flaky"))
        assert job.status == "done" and job.attempts == 3
        assert job.result == {"succeeded_on_attempt": 3}


def test_jobs_die_after_max_attempts(database, settings):
    with session_scope() as session:
        enqueue(session, "fail_then_succeed", {"succeed_on": 99}, idempotency_key="doomed", max_attempts=2)
    for _ in range(2):
        with session_scope() as session:
            job = session.scalar(select(Job).where(Job.idempotency_key == "doomed"))
            job.run_after = datetime.now(UTC)
        assert process_one(settings, "t1") is True
    with session_scope() as session:
        job = session.scalar(select(Job).where(Job.idempotency_key == "doomed"))
        assert job.status == "dead" and job.attempts == 2 and job.finished_at is not None
    assert process_one(settings, "t1") is False


def test_expired_lease_is_recovered_by_another_worker(database, settings):
    with session_scope() as session:
        enqueue(session, "echo", {}, idempotency_key="crashed")
    with session_scope() as session:
        job = claim_next(session, "crashed-worker", lease_seconds=60)
        assert job is not None and job.status == "leased"
        # simulate a worker that died: the lease expired without a result
        job.lease_expires_at = datetime.now(UTC) - timedelta(seconds=1)
    assert process_one(settings, "healthy-worker") is True
    with session_scope() as session:
        job = session.scalar(select(Job).where(Job.idempotency_key == "crashed"))
        assert job.status == "done" and job.attempts == 2


def test_backoff_is_bounded_and_jittered():
    delays = [backoff_delay(attempt) for attempt in range(1, 12)]
    assert all(0 <= d <= 300 for d in delays)
    assert backoff_delay(1) <= 2.0
