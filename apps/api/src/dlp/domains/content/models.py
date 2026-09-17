from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dlp.db.base import Base, new_id, utcnow


class Mission(Base):
    """A validated mission document (contract + scenarios + content pack) as loaded from `content/`."""

    __tablename__ = "missions"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    cefr_target: Mapped[str] = mapped_column(String(5), nullable=False)
    title_nl: Mapped[str] = mapped_column(String(200), nullable=False)
    title_fa: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    review_status: Mapped[str] = mapped_column(String(20), nullable=False, default="unreviewed")
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    document: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    fixed_word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    loaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    steps: Mapped[list[MissionStep]] = relationship(
        back_populates="mission", cascade="all, delete-orphan", order_by="MissionStep.position"
    )


class MissionStep(Base):
    """Normalised view of the ordered steps so that progress and evidence can join on them."""

    __tablename__ = "mission_steps"
    __table_args__ = (UniqueConstraint("mission_id", "key", name="uq_mission_steps_mission_key"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    mission_id: Mapped[str] = mapped_column(ForeignKey("missions.id", ondelete="CASCADE"), nullable=False)
    key: Mapped[str] = mapped_column(String(80), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    skill: Mapped[str] = mapped_column(String(20), nullable=False)
    step_type: Mapped[str] = mapped_column(String(20), nullable=False)
    variant: Mapped[str] = mapped_column(String(20), nullable=False, default="base")
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    mission: Mapped[Mission] = relationship(back_populates="steps")
