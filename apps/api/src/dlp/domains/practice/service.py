from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from dlp.db.base import utcnow
from dlp.domains.content.models import Mission
from dlp.domains.content.service import mission_document
from dlp.domains.practice.models import EvidenceRecord, PracticeSession


class PracticeError(Exception):
    def __init__(self, reason: str, status_code: int = 400) -> None:
        super().__init__(reason)
        self.reason = reason
        self.status_code = status_code


def start_session(session: Session, *, learner_id: uuid.UUID, mission: Mission, variant: str,
                  request_id: str) -> PracticeSession:
    """Idempotent on (learner, request_id): the same request returns the same session."""
    existing = session.scalar(
        select(PracticeSession).where(PracticeSession.learner_id == learner_id, PracticeSession.request_id == request_id)
    )
    if existing is not None:
        return existing
    document = mission_document(mission)
    if variant not in {scenario.variant for scenario in document.scenarios}:
        raise PracticeError(f"unknown variant {variant}")
    first_step = next(step for step in document.steps if step.variant == variant)
    practice = PracticeSession(
        learner_id=learner_id, mission_id=mission.id, variant=variant, status="active",
        current_step_key=first_step.key, request_id=request_id,
        state={"appointment": {}, "step_progress": {}},
    )
    session.add(practice)
    session.flush()
    return practice


def get_session_for_learner(session: Session, learner_id: uuid.UUID, session_id: uuid.UUID) -> PracticeSession:
    practice = session.get(PracticeSession, session_id)
    if practice is None or practice.learner_id != learner_id:
        raise PracticeError("session not found", status_code=404)
    return practice


def list_sessions(session: Session, learner_id: uuid.UUID) -> list[PracticeSession]:
    return list(
        session.scalars(
            select(PracticeSession).where(PracticeSession.learner_id == learner_id).order_by(PracticeSession.started_at.desc())
        )
    )


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
