from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from dlp.db.base import Base, new_id, utcnow

SKILLS: tuple[str, ...] = ("reading", "listening", "speaking", "writing")


class SkillRecord(Base):
    """Four separate records per learner and mission: one per skill, never merged into one score."""

    __tablename__ = "skill_records"
    __table_args__ = (UniqueConstraint("learner_id", "mission_id", "skill", name="uq_skill_records_learner_mission_skill"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"), nullable=False)
    mission_id: Mapped[str] = mapped_column(ForeignKey("missions.id", ondelete="CASCADE"), nullable=False)
    skill: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="not_started")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latest_assessment: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    evidence_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )
