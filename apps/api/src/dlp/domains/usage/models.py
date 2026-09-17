from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from dlp.db.base import Base, new_id, utcnow

METRICS: tuple[str, ...] = ("model_calls", "tokens", "audio_seconds")
SCOPES: tuple[str, ...] = ("daily", "total")


class UsageCounter(Base):
    """One counter per learner, scope, period and metric. `used + reserved` may never exceed `limit_value`."""

    __tablename__ = "usage_counters"
    __table_args__ = (
        UniqueConstraint("learner_id", "scope", "period_key", "metric", name="uq_usage_counters_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"), nullable=False)
    scope: Mapped[str] = mapped_column(String(10), nullable=False)
    period_key: Mapped[date] = mapped_column(Date, nullable=False)  # the day for `daily`, 1970-01-01 for `total`
    metric: Mapped[str] = mapped_column(String(30), nullable=False)
    used: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False, default=0)
    reserved: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False, default=0)
    limit_value: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )


class UsageReservation(Base):
    """A reservation made before an external call; committed or released afterwards. `request_id` deduplicates."""

    __tablename__ = "usage_reservations"
    __table_args__ = (
        UniqueConstraint("learner_id", "metric", "request_id", name="uq_usage_reservations_request"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"), nullable=False)
    metric: Mapped[str] = mapped_column(String(30), nullable=False)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    amount_reserved: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    amount_used: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False, default=0)
    state: Mapped[str] = mapped_column(String(12), nullable=False, default="reserved")  # reserved|committed|released
    period_key: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PricingEntry(Base):
    """Unit prices per provider SKU. Stays empty until Phase B records the authorised allowance."""

    __tablename__ = "pricing_entries"
    __table_args__ = (UniqueConstraint("provider", "sku", "effective_from", name="uq_pricing_entries_sku"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_id)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    sku: Mapped[str] = mapped_column(String(120), nullable=False)
    metric: Mapped[str] = mapped_column(String(30), nullable=False)
    unit: Mapped[str] = mapped_column(String(40), nullable=False)  # e.g. "1000 tokens", "hour"
    unit_price: Mapped[float] = mapped_column(Numeric(12, 6), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
