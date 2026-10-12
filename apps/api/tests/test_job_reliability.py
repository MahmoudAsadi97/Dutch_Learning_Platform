"""Release schema changes, long handlers and obsolete workers cannot silently alter queue ownership."""

from __future__ import annotations

import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import select, text

from dlp.db.session import session_scope
from dlp.domains.jobs import service
from dlp.domains.jobs.models import Job
from dlp.domains.jobs.schema import SchemaVersionMismatch, _packaged_heads, require_current_schema


class _HeadsResult:
    def __init__(self, heads: tuple[str, ...]) -> None:
        self.heads = heads

    def scalars(self) -> tuple[str, ...]:
        return self.heads


class _SchemaSession:
    def __init__(self, heads: tuple[str, ...]) -> None:
        self.heads = heads

    def execute(self, statement):
        assert str(statement) == "SELECT version_num FROM alembic_version"
        return _HeadsResult(self.heads)


def test_schema_guard_reads_the_packaged_migrations():
    api_dir = Path(__file__).resolve().parents[1]
    assert _packaged_heads(str(api_dir)) == frozenset({"0010"})


def test_schema_guard_accepts_exact_complete_heads(monkeypatch):
    monkeypatch.setattr("dlp.domains.jobs.schema._packaged_heads", lambda _: frozenset({"left", "right"}))
    require_current_schema(_SchemaSession(("right", "left")))


@pytest.mark.parametrize("actual", [("0007",), ("0011",), (), ("0010", "unexpected")])
def test_schema_guard_rejects_behind_ahead_missing_or_extra_heads(monkeypatch, actual):
    monkeypatch.setattr("dlp.domains.jobs.schema._packaged_heads", lambda _: frozenset({"0010"}))
    with pytest.raises(SchemaVersionMismatch):
        require_current_schema(_SchemaSession(actual))


def test_worker_checks_schema_before_sweeping_or_claiming(monkeypatch, settings):
    operations = []

    def incompatible(_):
        raise SchemaVersionMismatch("changed during release")

    monkeypatch.setattr(service, "require_current_schema", incompatible)
    monkeypatch.setattr(service, "sweep_expired", lambda _: operations.append("sweep"))
    monkeypatch.setattr(service, "claim_next", lambda *_: operations.append("claim"))
    with pytest.raises(SchemaVersionMismatch):
        service.process_one(settings, "old-image")
    assert operations == []


def _claimed_job(*, owner: str = "first-worker") -> tuple:
    with session_scope() as session:
        job = service.enqueue(session, "echo", {}, idempotency_key="lease-fence")
        job_id = job.id
    with session_scope() as session:
        job = service.claim_next(session, owner, lease_seconds=60)
        assert job is not None and job.id == job_id
        return job_id, job.attempts


def test_stale_owner_cannot_renew_or_finalize_a_new_attempt(database):
    job_id, old_attempt = _claimed_job()
    with session_scope() as session:
        job = session.get(Job, job_id)
        job.lease_expires_at = datetime.now(UTC) - timedelta(seconds=1)
    with session_scope() as session:
        replacement = service.claim_next(session, "replacement", lease_seconds=60)
        assert replacement is not None and replacement.attempts == old_attempt + 1
    with session_scope() as session:
        assert not service.renew_lease(session, job_id, "first-worker", old_attempt, 60)
        assert not service._finish_job(session, job_id, "first-worker", old_attempt,
                                       status="done", result={"obsolete": True})
    with session_scope() as session:
        job = session.get(Job, job_id)
        assert job.status == "leased" and job.lease_owner == "replacement" and job.result is None
        assert service._finish_job(session, job_id, "replacement", old_attempt + 1,
                                   status="done", result={"current": True})
    with session_scope() as session:
        job = session.get(Job, job_id)
        assert job.status == "done" and job.result == {"current": True}


def test_attempt_fence_also_protects_a_reused_worker_name(database):
    job_id, old_attempt = _claimed_job(owner="cli")
    with session_scope() as session:
        job = session.get(Job, job_id)
        job.lease_expires_at = datetime.now(UTC) - timedelta(seconds=1)
    with session_scope() as session:
        assert service.claim_next(session, "cli", lease_seconds=60).attempts == old_attempt + 1
    with session_scope() as session:
        assert not service.renew_lease(session, job_id, "cli", old_attempt, 60)
        assert not service._finish_job(session, job_id, "cli", old_attempt, status="queued")


def test_expired_owner_cannot_revive_or_finalize_its_lease(database):
    job_id, attempt = _claimed_job()
    with session_scope() as session:
        job = session.get(Job, job_id)
        job.lease_expires_at = datetime.now(UTC) - timedelta(seconds=1)
    with session_scope() as session:
        assert not service.renew_lease(session, job_id, "first-worker", attempt, 60)
        assert not service._finish_job(session, job_id, "first-worker", attempt, status="done", result={})


def test_long_handler_keeps_lease_and_cannot_be_reclaimed(database, settings, monkeypatch):
    started, renewed, finish = threading.Event(), threading.Event(), threading.Event()
    errors: list[BaseException] = []
    renewals = 0
    original_renew = service.renew_lease

    def renew(*args):
        nonlocal renewals
        result = original_renew(*args)
        if result:
            renewals += 1
            if renewals >= 4:  # more than the original one-second lease, with no arbitrary sleep
                renewed.set()
        return result

    @service.registry.register("long_lease_test")
    def long_handler(session, payload):
        started.set()
        assert finish.wait(5), "test did not release the handler"
        return {"completed": True}

    monkeypatch.setattr(service, "renew_lease", renew)
    with session_scope() as session:
        service.enqueue(session, "long_lease_test", {}, idempotency_key="long-handler")

    def run():
        try:
            service.process_one(settings.model_copy(update={"job_lease_seconds": 1}), "slow-worker")
        except BaseException as exc:  # capture thread errors so the test cannot pass accidentally
            errors.append(exc)

    worker = threading.Thread(target=run)
    worker.start()
    try:
        assert started.wait(3)
        assert renewed.wait(4), "the long-running handler did not renew its lease"
        assert not service.process_one(settings, "competing-worker")
        with session_scope() as session:
            job = session.scalar(select(Job).where(Job.idempotency_key == "long-handler"))
            assert job.status == "leased" and job.attempts == 1 and job.lease_owner == "slow-worker"
    finally:
        finish.set()
        worker.join(timeout=5)
    assert not worker.is_alive() and errors == []
    with session_scope() as session:
        job = session.scalar(select(Job).where(Job.idempotency_key == "long-handler"))
        assert job.status == "done" and job.result == {"completed": True} and job.attempts == 1


def test_live_worker_pauses_when_database_advances_to_a_new_image(database, settings):
    with session_scope() as session:
        service.enqueue(session, "echo", {}, idempotency_key="schema-release")
        current_heads = list(session.execute(text("SELECT version_num FROM alembic_version")).scalars())
    assert current_heads == ["0010"]
    try:
        with session_scope() as session:
            session.execute(text("UPDATE alembic_version SET version_num = '0011'"))
        with pytest.raises(SchemaVersionMismatch):
            service.process_one(settings, "previous-image")
    finally:
        with session_scope() as session:
            session.execute(text("UPDATE alembic_version SET version_num = :head"), {"head": current_heads[0]})
    with session_scope() as session:
        job = session.scalar(select(Job).where(Job.idempotency_key == "schema-release"))
        assert job.status == "queued" and job.attempts == 0
    assert service.process_one(settings, "current-image")
