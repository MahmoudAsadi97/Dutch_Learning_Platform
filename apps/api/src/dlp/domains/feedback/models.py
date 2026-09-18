from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from dlp.db.base import Base, new_id, utcnow


class FeedbackReport(Base):
    """One feedback report per request: what the model said about one step, every point tied to evidence ids
    that the code verified against the session before the report was stored."""

    __tablename__ = "feedback_reports"
    __table_args__ = (Index("ix_feedback_reports_session_step", "session_id", "step_key"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("practice_sessions.id", ondelete="CASCADE"), nullable=False
    )
    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"), nullable=False)
    step_key: Mapped[str] = mapped_column(String(80), nullable=False)
    skill: Mapped[str] = mapped_column(String(20), nullable=False)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    task_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    report: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    evidence_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    dropped_points: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    model_provider: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    model_name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    prompt_version: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
