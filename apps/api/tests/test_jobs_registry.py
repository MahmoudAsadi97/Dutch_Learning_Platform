"""Every handler is registered through one function; unknown kinds and stale leases cannot block the queue."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from dlp.db.session import session_scope
from dlp.domains.jobs.handlers import register_all
from dlp.domains.jobs.models import Job
from dlp.domains.jobs.service import drain, enqueue, process_one


def test_register_all_covers_every_enqueued_kind():
    assert {"story_episode", "content_review", "video_script", "video_render"} <= set(register_all())


def test_unknown_kind_is_dead_lettered_without_blocking_the_queue(database, settings):
    with session_scope() as session:
        # enqueue() refuses unknown kinds, so the row is written the way an older image would have left it
        session.add(Job(kind="nobody_handles_this", payload={}, idempotency_key="orphan",
                        run_after=datetime.now(UTC), max_attempts=5))
        enqueue(session, "echo", {"after": "orphan"}, idempotency_key="echo-after-orphan")
    assert drain(settings, worker_id="t-orphan") == 2
    with session_scope() as session:
        orphan = session.scalar(select(Job).where(Job.idempotency_key == "orphan"))
        echo = session.scalar(select(Job).where(Job.idempotency_key == "echo-after-orphan"))
        assert orphan.status == "dead" and orphan.attempts == 1 and "no handler registered" in orphan.last_error
        assert echo.status == "done"


def test_expired_lease_at_max_attempts_is_dead_not_rerun(database, settings):
    with session_scope() as session:
        enqueue(session, "fail_then_succeed", {"succeed_on": 99}, idempotency_key="stale-lease", max_attempts=2)
        job = session.scalar(select(Job).where(Job.idempotency_key == "stale-lease"))
        job.status = "leased"
        job.lease_owner = "crashed-worker"
        job.attempts = 2
        job.lease_expires_at = datetime.now(UTC) - timedelta(seconds=5)
    assert process_one(settings, "t-sweeper") is False
    with session_scope() as session:
        job = session.scalar(select(Job).where(Job.idempotency_key == "stale-lease"))
        assert job.status == "dead" and job.attempts == 2 and job.lease_owner == ""
        assert "lease expired on the last allowed attempt" in job.last_error


def test_enqueue_defaults_to_the_configured_attempt_limit(database, settings):
    with session_scope() as session:
        job = enqueue(session, "echo", {}, idempotency_key="default-attempts")
        assert job.max_attempts == settings.job_max_attempts
