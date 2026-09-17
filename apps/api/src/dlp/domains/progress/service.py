from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from dlp.domains.progress.models import SKILLS, SkillRecord


def ensure_skill_records(session: Session, learner_id: uuid.UUID, mission_id: str) -> list[SkillRecord]:
    """Create the four per-skill records for a learner and mission if they do not exist yet."""
    existing = {
        record.skill: record
        for record in session.scalars(
            select(SkillRecord).where(SkillRecord.learner_id == learner_id, SkillRecord.mission_id == mission_id)
        )
    }
    for skill in SKILLS:
        if skill not in existing:
            record = SkillRecord(learner_id=learner_id, mission_id=mission_id, skill=skill)
            session.add(record)
            existing[skill] = record
    session.flush()
    return [existing[skill] for skill in SKILLS]


def skill_records_for(session: Session, learner_id: uuid.UUID) -> list[SkillRecord]:
    return list(
        session.scalars(
            select(SkillRecord).where(SkillRecord.learner_id == learner_id).order_by(SkillRecord.mission_id, SkillRecord.skill)
        )
    )
