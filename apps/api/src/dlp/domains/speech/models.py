from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from dlp.db.base import Base, new_id, utcnow


class AudioAsset(Base):
    """Metadata for one stored audio file (learner recording or synthesised reply)."""

    __tablename__ = "audio_assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    learner_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("learners.id", ondelete="CASCADE"), nullable=True
    )
    kind: Mapped[str] = mapped_column(String(20), nullable=False)  # recording | synthesis | fixed
    blob_key: Mapped[str] = mapped_column(String(300), nullable=False, unique=True)
    container: Mapped[str] = mapped_column(String(80), nullable=False)
    source_container_format: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    source_codec: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    source_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sample_rate: Mapped[int] = mapped_column(Integer, nullable=False, default=16000)
    channels: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    label: Mapped[str] = mapped_column(String(60), nullable=False, default="")
    provider: Mapped[str] = mapped_column(String(60), nullable=False, default="")
    request_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
