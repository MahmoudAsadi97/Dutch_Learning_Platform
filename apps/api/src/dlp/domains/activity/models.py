from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from dlp.db.base import Base, new_id, utcnow


class ActivityEvent(Base):
    """One countable action of a learner: reading an episode, answering its questions, reviewing a word.

    Append-only. (learner_id, kind, dedupe_key) is unique, so the same action is recorded once however often
    it is retried; `dedupe_key` follows the kind's scope in `rules.py`. `points` is what it earned (zero once
    a cap or a repeat applies), `units` how much of it there was (correct questions, words)."""

    __tablename__ = "activity_events"
    __table_args__ = (
        UniqueConstraint("learner_id", "kind", "dedupe_key"),
        Index("ix_activity_events_learner_day", "learner_id", "day"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"), nullable=False)
    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    ref: Mapped[str] = mapped_column(String(200), nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(240), nullable=False)
    day: Mapped[date] = mapped_column(Date, nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    units: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    skill: Mapped[str | None] = mapped_column(String(20), nullable=True)
    request_id: Mapped[str] = mapped_column(String(80), nullable=False, default="", server_default="")
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


class LearningDay(Base):
    """One row per learner per calendar day (Europe/Brussels): the points of that day's events, what they
    were for, and the daily goal in force at the day's latest activity."""

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
    exercise_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    exercise_sessions: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    goal_target: Mapped[int | None] = mapped_column(Integer, nullable=True)
    goal_met: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow,
                                                 onupdate=utcnow)
