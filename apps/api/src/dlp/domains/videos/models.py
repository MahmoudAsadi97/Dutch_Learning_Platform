"""A video lesson: a short presenter video in Belgian Dutch at the learner's level, about a topic they chose.

The script is written by the chat model and checked by the story validator; the picture and the voice
come from the configured renderer (an Azure text-to-speech avatar in production, drawn scene cards with
the local voice on a laptop). The finished file lives in blob storage; subtitles are kept here as cues.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from dlp.db.base import Base, new_id, utcnow


class VideoLesson(Base):
    __tablename__ = "video_lessons"
    __table_args__ = (Index("ix_video_lessons_learner_status", "learner_id", "status", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"), nullable=False)
    stage_id: Mapped[str] = mapped_column(String(20), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False, default="uitleg")  # uitleg | verhaal
    topic: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    topic_id: Mapped[str] = mapped_column(String(60), nullable=False, default="")
    # queued → writing → rendering → ready | failed
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="queued")
    error_code: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    title: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    scenes: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    glossary: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    questions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    checks: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    provider: Mapped[str] = mapped_column(String(60), nullable=False, default="")
    model: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    prompt_version: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    renderer: Mapped[str] = mapped_column(String(60), nullable=False, default="")
    render_job_id: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    render_polls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    voice: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    presenter: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    media_key: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    media_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cues: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    answers: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    rating: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    watched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow,
                                                 onupdate=utcnow)
