from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from dlp.db.base import Base, new_id, utcnow

EPISODE_STATUSES: tuple[str, ...] = ("queued", "generating", "ready", "failed")


class StorySeries(Base):
    """One continuing serial per learner: the setting, the cast and a rolling memory of what happened."""

    __tablename__ = "story_series"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"), nullable=False,
                                                  unique=True)
    stage_id: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    bible: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    memory: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    episode_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow,
                                                 onupdate=utcnow)


class StoryEpisode(Base):
    """A generated episode. Only a validated draft reaches `ready`; the learner never sees a rejected one."""

    __tablename__ = "story_episodes"
    __table_args__ = (
        UniqueConstraint("series_id", "number"),
        Index("ix_story_episodes_learner_status", "learner_id", "status", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"), nullable=False)
    series_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("story_series.id", ondelete="CASCADE"), nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    stage_id: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="queued")
    error_code: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    theme: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    theme_source: Mapped[str] = mapped_column(String(20), nullable=False, default="auto")
    topic_id: Mapped[str] = mapped_column(String(60), nullable=False, default="")
    previous_choice: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    title: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    paragraphs: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    glossary: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    questions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    choices: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    recap: Mapped[str] = mapped_column(Text, nullable=False, default="")
    mood: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    checks: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    provider: Mapped[str] = mapped_column(String(60), nullable=False, default="")
    model: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    prompt_version: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    answers: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    chosen_choice: Mapped[str] = mapped_column(String(8), nullable=False, default="")
    rating: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow,
                                                 onupdate=utcnow)


class VocabItem(Base):
    """A word the learner chose to keep. Scheduled with spaced repetition; never silently removed."""

    __tablename__ = "vocab_items"
    __table_args__ = (
        UniqueConstraint("learner_id", "key"),
        Index("ix_vocab_items_learner_due", "learner_id", "due_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"), nullable=False)
    key: Mapped[str] = mapped_column(String(120), nullable=False)
    term: Mapped[str] = mapped_column(String(120), nullable=False)
    meaning_en: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    meaning_fa: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    example: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source_kind: Mapped[str] = mapped_column(String(20), nullable=False, default="story")
    source_id: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    ease: Mapped[float] = mapped_column(Float, nullable=False, default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    repetitions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lapses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_grade: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_request_id: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


class LearningDay(Base):
    """One row per learner per calendar day (Europe/Brussels) with the points earned that day."""

    __tablename__ = "learning_days"
    __table_args__ = (UniqueConstraint("learner_id", "day"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"), nullable=False)
    day: Mapped[date] = mapped_column(Date, nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    episodes_read: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    words_reviewed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    questions_correct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    read_aloud: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    videos_watched: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    goal_met: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow,
                                                 onupdate=utcnow)
