from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from dlp.db.base import utcnow
from dlp.domains.content.models import Mission
from dlp.domains.content.schemas import CheckpointPayload, MissionDocument
from dlp.domains.content.service import mission_document
from dlp.domains.practice.models import EvidenceRecord, PracticeSession


class PracticeError(Exception):
    def __init__(self, reason: str, status_code: int = 400) -> None:
        super().__init__(reason)
        self.reason = reason
        self.status_code = status_code


def variant_allows_retry(document: MissionDocument, variant: str) -> bool:
    """A variant whose checkpoint forbids retry gets exactly one session per learner."""
    for step in document.steps:
        if step.variant == variant and isinstance(step.payload, CheckpointPayload):
            return step.payload.restrictions.retry
    return True


def start_session(session: Session, *, learner_id: uuid.UUID, mission: Mission, variant: str,
                  request_id: str) -> PracticeSession:
    """Idempotent on (learner, request_id); resumes the active session of the same variant instead of opening a second one.

    A variant whose checkpoint has `retry: false` cannot be started again once its only session is over.
    """
    existing = session.scalar(
        select(PracticeSession).where(PracticeSession.learner_id == learner_id, PracticeSession.request_id == request_id)
    )
    if existing is not None:
        return existing
    document = mission_document(mission)
    if variant not in {scenario.variant for scenario in document.scenarios}:
        raise PracticeError(f"unknown variant {variant}")
    previous = list(session.scalars(
        select(PracticeSession)
        .where(PracticeSession.learner_id == learner_id, PracticeSession.mission_id == mission.id,
               PracticeSession.variant == variant)
        .order_by(PracticeSession.started_at.desc())
    ))
    active = next((p for p in previous if p.status == "active"), None)
    if active is not None:
        return active
    if previous and not variant_allows_retry(document, variant):
        raise PracticeError("this checkpoint allows no retry; the earlier attempt stands", status_code=409)
    first_step = next(step for step in document.steps if step.variant == variant)
    practice = PracticeSession(
        learner_id=learner_id, mission_id=mission.id, variant=variant, status="active",
        current_step_key=first_step.key, request_id=request_id,
        state={"appointment": {}, "step_progress": {}},
    )
    session.add(practice)
    session.flush()
    return practice


def abandon_session(session: Session, practice: PracticeSession) -> PracticeSession:
    """Close an active session without completing it. Its turns and evidence stay; a checkpoint attempt stays used."""
    if practice.status != "active":
        raise PracticeError("this session is already closed", status_code=409)
    practice.status = "abandoned"
    practice.completed_at = utcnow()
    practice.updated_at = utcnow()
    session.flush()
    return practice


def get_session_for_learner(session: Session, learner_id: uuid.UUID, session_id: uuid.UUID) -> PracticeSession:
    practice = session.get(PracticeSession, session_id)
    if practice is None or practice.learner_id != learner_id:
        raise PracticeError("session not found", status_code=404)
    return practice


def list_sessions(session: Session, learner_id: uuid.UUID, *, mission_id: str | None = None,
                  variant: str | None = None, status: str | None = None) -> list[PracticeSession]:
    query = select(PracticeSession).where(PracticeSession.learner_id == learner_id)
    if mission_id:
        query = query.where(PracticeSession.mission_id == mission_id)
    if variant:
        query = query.where(PracticeSession.variant == variant)
    if status:
        query = query.where(PracticeSession.status == status)
    return list(session.scalars(query.order_by(PracticeSession.started_at.desc())))


def record_evidence(session: Session, practice: PracticeSession, *, step_key: str, skill: str, kind: str,
                    modality: str, payload: dict, source: str = "application",
                    turn_id: uuid.UUID | None = None) -> EvidenceRecord:
    record = EvidenceRecord(
        session_id=practice.id, turn_id=turn_id, step_key=step_key, skill=skill, kind=kind,
        modality=modality, payload=payload, source=source,
    )
    session.add(record)
    practice.updated_at = utcnow()
    session.flush()
    return record
