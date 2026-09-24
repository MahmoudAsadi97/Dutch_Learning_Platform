from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from dlp.db.base import Base, new_id, utcnow


class CurriculumPractice(Base):
    __tablename__ = "curriculum_practice"
    __table_args__ = (UniqueConstraint("learner_id", "stage_id", "skill"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"), nullable=False)
    stage_id: Mapped[str] = mapped_column(String(20), nullable=False)
    skill: Mapped[str] = mapped_column(String(20), nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


class CurriculumAttempt(Base):
    __tablename__ = "curriculum_attempts"
    __table_args__ = (
        UniqueConstraint("learner_id", "request_id"),
        Index("ix_curriculum_attempts_learner_stage", "learner_id", "stage_id"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"), nullable=False)
    stage_id: Mapped[str] = mapped_column(String(20), nullable=False)
    request_id: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="in_progress")
    content_version: Mapped[str] = mapped_column(String(64), nullable=False)
    test_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    submission: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    results: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    # An audio recording can support one final attempt only. Learner deletion cascades through both.
    speaking_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("audio_assets.id", ondelete="SET NULL"), nullable=True, unique=True,
    )
    admin_preview: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TopicPractice(Base):
    """One latest response per learner/topic/skill; completion survives unsuccessful retries."""
    __tablename__ = "topic_practice"
    __table_args__ = (UniqueConstraint("learner_id", "stage_id", "topic_id", "skill"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"), nullable=False)
    stage_id: Mapped[str] = mapped_column(String(20), nullable=False)
    topic_id: Mapped[str] = mapped_column(String(60), nullable=False)
    skill: Mapped[str] = mapped_column(String(20), nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    latest_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    content_version: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
