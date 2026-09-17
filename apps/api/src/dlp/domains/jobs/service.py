"""Durable background jobs on PostgreSQL: enqueue, claim with a lease, retry with backoff, recover on restart."""

from __future__ import annotations

import logging
import random
import socket
import threading
import time
import traceback
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from dlp.config import Settings
from dlp.db.session import session_scope
from dlp.domains.jobs.models import Job

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
              max_attempts=max_attempts if max_attempts is not None else 5)
    session.add(job)
    session.flush()
    return job


def claim_next(session: Session, worker_id: str, lease_seconds: int) -> Job | None:
    """Claim one runnable job (queued and due, or leased but expired) with SKIP LOCKED."""
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
                       OR (status = 'leased' AND lease_expires_at < :now)
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


def run_job(session: Session, job: Job, settings: Settings) -> None:
    handler = registry.get(job.kind)
    payload = dict(job.payload)
    payload["_attempt"] = job.attempts
    try:
        result = handler(session, payload)
    except Exception as exc:  # noqa: BLE001 - every failure is recorded on the job row
        job.last_error = f"{exc.__class__.__name__}: {exc}\n{traceback.format_exc()[-2000:]}"
        now = datetime.now(UTC)
        if job.attempts >= job.max_attempts:
            job.status = "dead"
            job.finished_at = now
            log.warning("job %s (%s) is dead after %s attempts", job.id, job.kind, job.attempts)
        else:
            job.status = "queued"
            job.run_after = now + timedelta(seconds=backoff_delay(job.attempts))
            job.lease_owner = ""
            job.lease_expires_at = None
        return
    job.status = "done"
    job.result = result or {}
    job.finished_at = datetime.now(UTC)
    job.lease_owner = ""
    job.lease_expires_at = None


def process_one(settings: Settings, worker_id: str) -> bool:
    """Claim and run one job in its own transaction. Returns True when a job was processed."""
    with session_scope() as session:
        job = claim_next(session, worker_id, settings.job_lease_seconds)
        if job is None:
            return False
        session.commit()  # the lease is durable before the handler runs
    with session_scope() as session:
        job = session.get(Job, job.id)
        assert job is not None
        if job.lease_owner != worker_id:
            return True
        run_job(session, job, settings)
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
            except Exception:  # noqa: BLE001 - the loop must survive database hiccups
                log.exception("job loop iteration failed")
                time.sleep(min(self.settings.job_poll_interval_seconds * 5, 30))
                continue
            self._stop.wait(self.settings.job_poll_interval_seconds)
        log.info("job loop stopped after %s jobs", self.processed)
