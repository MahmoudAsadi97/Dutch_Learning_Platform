from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dlp.db.base import Base, new_id, utcnow


class PracticeSession(Base):
    """One attempt at a mission variant by one learner."""

    __tablename__ = "practice_sessions"
    __table_args__ = (
        UniqueConstraint("learner_id", "request_id", name="uq_practice_sessions_learner_request"),
        Index("ix_practice_sessions_learner_status", "learner_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"), nullable=False)
    mission_id: Mapped[str] = mapped_column(ForeignKey("missions.id", ondelete="RESTRICT"), nullable=False)
    variant: Mapped[str] = mapped_column(String(20), nullable=False, default="base")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    current_step_key: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    turns: Mapped[list[PracticeTurn]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="PracticeTurn.turn_index"
    )
    evidence: Mapped[list[EvidenceRecord]] = relationship(back_populates="session", cascade="all, delete-orphan")


class PracticeTurn(Base):
    """One exchange inside a session: what the learner produced and what the character answered."""

    __tablename__ = "practice_turns"
    __table_args__ = (
        UniqueConstraint("session_id", "turn_index", name="uq_practice_turns_session_index"),
        UniqueConstraint("session_id", "request_id", name="uq_practice_turns_session_request"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("practice_sessions.id", ondelete="CASCADE"), nullable=False
    )
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False)
    step_key: Mapped[str] = mapped_column(String(80), nullable=False)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    modality: Mapped[str] = mapped_column(String(20), nullable=False)  # speech | typed
    learner_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    learner_audio_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("audio_assets.id", ondelete="SET NULL"), nullable=True
    )
    character_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    character_audio_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("audio_assets.id", ondelete="SET NULL"), nullable=True
    )
    proposed_action: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    action_result: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    model_meta: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    session: Mapped[PracticeSession] = relationship(back_populates="turns")


class EvidenceRecord(Base):
    """A piece of evidence that feedback and skill records may cite by id."""

    __tablename__ = "evidence_records"
    __table_args__ = (Index("ix_evidence_records_session_skill", "session_id", "skill"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("practice_sessions.id", ondelete="CASCADE"), nullable=False
    )
    turn_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("practice_turns.id", ondelete="SET NULL"), nullable=True
    )
    step_key: Mapped[str] = mapped_column(String(80), nullable=False)
    skill: Mapped[str] = mapped_column(String(20), nullable=False)
    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    modality: Mapped[str] = mapped_column(String(20), nullable=False, default="none")
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    source: Mapped[str] = mapped_column(String(80), nullable=False, default="application")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    session: Mapped[PracticeSession] = relationship(back_populates="evidence")
