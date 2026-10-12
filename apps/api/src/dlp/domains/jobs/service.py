"""Durable background jobs on PostgreSQL: enqueue, claim with a lease, retry with backoff, recover on restart."""

from __future__ import annotations

import json
import logging
import random
import socket
import threading
import traceback
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from dlp.config import Settings, get_settings
from dlp.db.session import session_scope
from dlp.domains.jobs.models import Job
from dlp.domains.jobs.schema import require_current_schema

log = logging.getLogger(__name__)

Handler = Callable[[Session, dict[str, Any]], dict[str, Any] | None]


class JobRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, Handler] = {}

    def register(self, kind: str) -> Callable[[Handler], Handler]:
        def decorator(func: Handler) -> Handler:
            self._handlers[kind] = func
            return func

        return decorator

    def get(self, kind: str) -> Handler:
        try:
            return self._handlers[kind]
        except KeyError as exc:
            raise KeyError(f"no handler registered for job kind {kind!r}") from exc

    def kinds(self) -> list[str]:
        return sorted(self._handlers)


registry = JobRegistry()


@registry.register("echo")
def _echo(session: Session, payload: dict[str, Any]) -> dict[str, Any]:
    return {"echo": payload}


@registry.register("fail_then_succeed")
def _fail_then_succeed(session: Session, payload: dict[str, Any]) -> dict[str, Any]:
    """Failure-injection handler used by tests: fails until `attempt` reaches `succeed_on`."""
    attempt = int(payload.get("_attempt", 0))
    if attempt < int(payload.get("succeed_on", 2)):
        raise RuntimeError(f"injected failure on attempt {attempt}")
    return {"succeeded_on_attempt": attempt}


def enqueue(session: Session, kind: str, payload: dict[str, Any], *, idempotency_key: str,
            run_after: datetime | None = None, max_attempts: int | None = None) -> Job:
    """Insert once per idempotency key; a duplicate returns the existing job unchanged."""
    registry.get(kind)  # fail fast on unknown kinds
    existing = session.execute(
        text("SELECT id FROM jobs WHERE idempotency_key = :key"), {"key": idempotency_key}
    ).first()
    if existing is not None:
        job = session.get(Job, existing[0])
        assert job is not None
        return job
    job = Job(kind=kind, payload=payload, idempotency_key=idempotency_key,
              run_after=run_after or datetime.now(UTC),
              max_attempts=max_attempts if max_attempts is not None else get_settings().job_max_attempts)
    session.add(job)
    session.flush()
    return job


def sweep_expired(session: Session) -> int:
    """A job whose lease expired on its last allowed attempt is dead; it must not run once more."""
    now = datetime.now(UTC)
    result = session.execute(
        text(
            """
            UPDATE jobs
               SET status = 'dead', finished_at = :now, updated_at = :now, lease_owner = '', lease_expires_at = NULL,
                   last_error = coalesce(last_error, '') || :note
             WHERE status = 'leased' AND lease_expires_at < :now AND attempts >= max_attempts
            """
        ),
        {"now": now, "note": "\nlease expired on the last allowed attempt"},
    )
    return result.rowcount or 0


def claim_next(session: Session, worker_id: str, lease_seconds: int) -> Job | None:
    """Claim one runnable job (queued and due, or leased but expired with attempts left) with SKIP LOCKED."""
    now = datetime.now(UTC)
    row = session.execute(
        text(
            """
            UPDATE jobs
               SET status = 'leased', lease_owner = :worker, lease_expires_at = :expires,
                   attempts = attempts + 1, updated_at = :now
             WHERE id = (
                   SELECT id FROM jobs
                    WHERE (status = 'queued' AND run_after <= :now)
                       OR (status = 'leased' AND lease_expires_at < :now AND attempts < max_attempts)
                    ORDER BY run_after
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1)
         RETURNING id
            """
        ),
        {"worker": worker_id, "expires": now + timedelta(seconds=lease_seconds), "now": now},
    ).first()
    if row is None:
        return None
    job = session.get(Job, row[0])
    session.refresh(job)
    return job


def backoff_delay(attempt: int, base: float = 2.0, cap: float = 300.0) -> float:
    """Exponential backoff with full jitter: random in [0, min(cap, base * 2**attempt)]."""
    return random.uniform(0, min(cap, base * (2 ** max(attempt - 1, 0))))


def renew_lease(session: Session, job_id: uuid.UUID, worker_id: str, attempt: int, lease_seconds: int) -> bool:
    """Only the current, still-live attempt may extend a lease; an expired lease cannot be revived."""
    now = datetime.now(UTC)
    result = session.execute(
        text("""
            UPDATE jobs SET lease_expires_at = :expires, updated_at = :now
             WHERE id = :id AND status = 'leased' AND lease_owner = :worker
               AND attempts = :attempt AND lease_expires_at > :now
        """),
        {"id": job_id, "worker": worker_id, "attempt": attempt,
         "now": now, "expires": now + timedelta(seconds=lease_seconds)},
    )
    return result.rowcount == 1


class _LeaseHeartbeat:
    """Renew in short independent transactions while the handler performs slow external work.

    Losing a lease does not cancel an external request or undo a handler's earlier commits.
    Handlers remain responsible for their domain's at-most-once and idempotency checks.
    """

    def __init__(self, job_id: uuid.UUID, worker_id: str, attempt: int, lease_seconds: int) -> None:
        self.job_id, self.worker_id, self.attempt = job_id, worker_id, attempt
        self.lease_seconds = lease_seconds
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="job-lease", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=2.0)

    def _run(self) -> None:
        interval = max(0.1, self.lease_seconds / 3)
        while not self._stop.wait(interval):
            try:
                with session_scope() as session:
                    require_current_schema(session)
                    if not renew_lease(session, self.job_id, self.worker_id, self.attempt, self.lease_seconds):
                        log.warning("job %s lease is no longer owned by this attempt", self.job_id)
                        return
            except Exception as exc:  # noqa: BLE001 - bounded retry; no credentials or payload in logs
                log.warning("job %s lease renewal failed (%s)", self.job_id, exc.__class__.__name__)


def _finish_job(session: Session, job_id: uuid.UUID, worker_id: str, attempt: int, *,
                status: str, result: dict[str, Any] | None = None, error: str = "",
                run_after: datetime | None = None) -> bool:
    """Fence completion and retry: a stale owner cannot overwrite a newer attempt's queue state."""
    require_current_schema(session)
    now = datetime.now(UTC)
    session.flush()  # write this handler's domain changes before the fenced queue transition
    updated = session.execute(
        text("""
            UPDATE jobs
               SET status = :status, result = CAST(:result AS jsonb), last_error = :error,
                   finished_at = :finished, run_after = coalesce(:run_after, run_after),
                   lease_owner = '', lease_expires_at = NULL, updated_at = :now
             WHERE id = :id AND status = 'leased' AND lease_owner = :worker
               AND attempts = :attempt AND lease_expires_at > :now
        """),
        {"id": job_id, "worker": worker_id, "attempt": attempt, "status": status,
         "result": json.dumps(result) if result is not None else None, "error": error,
         "finished": now if status in {"done", "dead"} else None, "run_after": run_after, "now": now},
    )
    if updated.rowcount != 1:
        # Only uncommitted changes can be discarded here. A handler may already have committed
        # its own durable claim; that is why domain handlers must also reject obsolete work.
        session.rollback()
        log.warning("job %s completion ignored: this attempt no longer owns a live lease", job_id)
        return False
    return True


def run_job(session: Session, job: Job, settings: Settings) -> None:
    job_id, worker_id, attempt, max_attempts = job.id, job.lease_owner, job.attempts, job.max_attempts
    payload = dict(job.payload)
    payload["_attempt"] = attempt
    try:
        handler = registry.get(job.kind)
    except KeyError as exc:
        # A kind nobody handles will never succeed on retry: dead-letter it so the queue keeps moving.
        _finish_job(session, job_id, worker_id, attempt, status="dead", error=f"{exc.__class__.__name__}: {exc}")
        log.warning("job %s has unknown kind %r", job_id, job.kind)
        return
    try:
        result = handler(session, payload)
    except Exception as exc:  # noqa: BLE001 - every failure is recorded on the job row
        error = f"{exc.__class__.__name__}: {exc}\n{traceback.format_exc()[-2000:]}"
        session.rollback()  # an SQL error may have left the handler's transaction unusable
        dead = attempt >= max_attempts
        _finish_job(session, job_id, worker_id, attempt, status="dead" if dead else "queued", error=error,
                    run_after=None if dead else datetime.now(UTC) + timedelta(seconds=backoff_delay(attempt)))
        return
    _finish_job(session, job_id, worker_id, attempt, status="done", result=result or {})


def process_one(settings: Settings, worker_id: str) -> bool:
    """Claim and run one job in its own transaction. Returns True when a job was processed."""
    with session_scope() as session:
        require_current_schema(session)
        sweep_expired(session)
        job = claim_next(session, worker_id, settings.job_lease_seconds)
        if job is None:
            return False
        session.commit()  # the lease is durable before the handler runs
        claimed_attempt = job.attempts
    with session_scope() as session:
        job = session.get(Job, job.id)
        assert job is not None
        if (job.status != "leased" or job.lease_owner != worker_id or job.attempts != claimed_attempt
                or job.lease_expires_at is None or job.lease_expires_at <= datetime.now(UTC)):
            return True
        heartbeat = _LeaseHeartbeat(job.id, worker_id, job.attempts, settings.job_lease_seconds)
        heartbeat.start()
        try:
            run_job(session, job, settings)
        finally:
            heartbeat.stop()
    return True


def drain(settings: Settings, worker_id: str = "test-worker", limit: int = 100) -> int:
    """Run jobs until none is runnable (tests and one-shot scripts)."""
    processed = 0
    while processed < limit and process_one(settings, worker_id):
        processed += 1
    return processed


class JobLoop:
    """Bounded in-process worker thread. One loop per API process; safe to run several processes."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.worker_id = f"{socket.gethostname()}-{uuid.uuid4().hex[:8]}"
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.processed = 0

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, name="job-loop", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 10.0) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            self._thread = None

    def _run(self) -> None:
        log.info("job loop started as %s", self.worker_id)
        while not self._stop.is_set():
            try:
                if process_one(self.settings, self.worker_id):
                    self.processed += 1
                    continue
            except Exception as exc:  # noqa: BLE001 - the loop must survive database hiccups
                log.warning("job loop iteration failed (%s); retrying later", exc.__class__.__name__)
                self._stop.wait(min(self.settings.job_poll_interval_seconds * 5, 30))
                continue
            self._stop.wait(self.settings.job_poll_interval_seconds)
        log.info("job loop stopped after %s jobs", self.processed)

