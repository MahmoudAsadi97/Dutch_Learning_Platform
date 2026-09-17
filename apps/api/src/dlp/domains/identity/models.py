from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from dlp.db.base import Base, new_id, utcnow


class Learner(Base):
    """One row per allowlisted person. Release 0.1 has exactly one learner."""

    __tablename__ = "learners"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    subject: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    identity_provider: Mapped[str] = mapped_column(String(40), nullable=False, default="fixture")
    support_language: Mapped[str] = mapped_column(String(10), nullable=False, default="fa")
    target_language: Mapped[str] = mapped_column(String(10), nullable=False, default="nl-BE")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
