from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from dlp.db.base import Base, new_id, utcnow


class LearnerProfile(Base):
    """The one source of a learner's level, daily goal and support language.

    Every screen that used to decide the level for itself (the practice coach, the serial, the videos)
    reads this row. `features` carries the per-learner switches of later phases (agents, voice)."""

    __tablename__ = "learner_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    learner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("learners.id", ondelete="CASCADE"),
                                                  unique=True, nullable=False)
    stage_id: Mapped[str] = mapped_column(String(20), nullable=False, default="a1")
    daily_goal_points: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    support_mode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    gloss_mode: Mapped[str] = mapped_column(String(8), nullable=False, default="auto")
    stated_goal: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    features: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    onboarded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
