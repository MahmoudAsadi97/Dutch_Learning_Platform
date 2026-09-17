"""Usage counters: atomic check-and-reserve before any external call, commit or release after it.

Limits are enforced in SQL: the reserve statement only succeeds when
`used + reserved + amount <= limit_value` for both the daily and the total
counter, inside one transaction. A repeated `request_id` returns the existing
reservation instead of reserving twice.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from dlp.config import Settings
from dlp.db.base import utcnow
from dlp.domains.usage.models import METRICS, PricingEntry, UsageCounter, UsageReservation

TOTAL_PERIOD_KEY = date(1970, 1, 1)


class UsageLimitExceeded(Exception):
    def __init__(self, metric: str, scope: str, requested: float, remaining: float) -> None:
        super().__init__(f"{scope} limit for {metric} exceeded: requested {requested}, remaining {remaining}")
        self.metric = metric
        self.scope = scope
        self.requested = requested
        self.remaining = remaining


@dataclass(frozen=True)
class Reservation:
    id: uuid.UUID
    metric: str
    amount: float
    deduplicated: bool


def limits_for(settings: Settings, metric: str) -> tuple[float, float]:
    mapping = {
        "model_calls": (settings.usage_daily_model_calls, settings.usage_total_model_calls),
        "tokens": (settings.usage_daily_tokens, settings.usage_total_tokens),
        "audio_seconds": (settings.usage_daily_audio_seconds, settings.usage_total_audio_seconds),
    }
    if metric not in mapping:
        raise ValueError(f"unknown metric {metric}")
    return mapping[metric]


def _today() -> date:
    return datetime.now(UTC).date()


def _ensure_counter(session: Session, learner_id: uuid.UUID, scope: str, period_key: date, metric: str,
                    limit_value: float) -> None:
    session.execute(
        text(
            """
            INSERT INTO usage_counters (id, learner_id, scope, period_key, metric, used, reserved, limit_value, updated_at)
            VALUES (:id, :learner_id, :scope, :period_key, :metric, 0, 0, :limit_value, :now)
            ON CONFLICT (learner_id, scope, period_key, metric) DO UPDATE SET limit_value = EXCLUDED.limit_value
            """
        ),
        {"id": uuid.uuid4(), "learner_id": learner_id, "scope": scope, "period_key": period_key,
         "metric": metric, "limit_value": limit_value, "now": utcnow()},
    )


def _try_reserve(session: Session, learner_id: uuid.UUID, scope: str, period_key: date, metric: str,
                 amount: float) -> bool:
    row = session.execute(
        text(
            """
            UPDATE usage_counters
               SET reserved = reserved + :amount, updated_at = :now
             WHERE learner_id = :learner_id AND scope = :scope AND period_key = :period_key AND metric = :metric
               AND used + reserved + :amount <= limit_value
         RETURNING id
            """
        ),
        {"amount": amount, "now": utcnow(), "learner_id": learner_id, "scope": scope,
         "period_key": period_key, "metric": metric},
    ).first()
    return row is not None


def remaining(session: Session, learner_id: uuid.UUID, scope: str, period_key: date, metric: str) -> float:
    counter = session.scalar(
        select(UsageCounter).where(
            UsageCounter.learner_id == learner_id, UsageCounter.scope == scope,
            UsageCounter.period_key == period_key, UsageCounter.metric == metric,
        )
    )
    if counter is None:
        return 0.0
    return float(Decimal(counter.limit_value) - Decimal(counter.used) - Decimal(counter.reserved))


def reserve(session: Session, settings: Settings, learner_id: uuid.UUID, metric: str, amount: float,
            request_id: str) -> Reservation:
    """Reserve `amount` of `metric` for today and for the total. Raises UsageLimitExceeded; deduplicates."""
    if amount <= 0:
        raise ValueError("amount must be positive")
    existing = session.scalar(
        select(UsageReservation).where(
            UsageReservation.learner_id == learner_id, UsageReservation.metric == metric,
            UsageReservation.request_id == request_id,
        )
    )
    if existing is not None:
        return Reservation(id=existing.id, metric=metric, amount=float(existing.amount_reserved), deduplicated=True)

    daily_limit, total_limit = limits_for(settings, metric)
    today = _today()
    with session.begin_nested():
        _ensure_counter(session, learner_id, "daily", today, metric, daily_limit)
        _ensure_counter(session, learner_id, "total", TOTAL_PERIOD_KEY, metric, total_limit)
        if not _try_reserve(session, learner_id, "daily", today, metric, amount):
            left = remaining(session, learner_id, "daily", today, metric)
            raise UsageLimitExceeded(metric, "daily", amount, left)
        if not _try_reserve(session, learner_id, "total", TOTAL_PERIOD_KEY, metric, amount):
            left = remaining(session, learner_id, "total", TOTAL_PERIOD_KEY, metric)
            raise UsageLimitExceeded(metric, "total", amount, left)
        reservation = UsageReservation(
            learner_id=learner_id, metric=metric, request_id=request_id,
            amount_reserved=amount, period_key=today,
        )
        session.add(reservation)
        session.flush()
    return Reservation(id=reservation.id, metric=metric, amount=amount, deduplicated=False)


def _settle(session: Session, reservation_id: uuid.UUID, actual: float | None) -> UsageReservation:
    reservation = session.get(UsageReservation, reservation_id)
    if reservation is None:
        raise ValueError("unknown reservation")
    if reservation.state != "reserved":
        return reservation
    reserved = float(reservation.amount_reserved)
    used = 0.0 if actual is None else max(0.0, float(actual))
    for scope, period_key in (("daily", reservation.period_key), ("total", TOTAL_PERIOD_KEY)):
        session.execute(
            text(
                """
                UPDATE usage_counters
                   SET reserved = GREATEST(reserved - :reserved, 0), used = used + :used, updated_at = :now
                 WHERE learner_id = :learner_id AND scope = :scope AND period_key = :period_key AND metric = :metric
                """
            ),
            {"reserved": reserved, "used": used, "now": utcnow(), "learner_id": reservation.learner_id,
             "scope": scope, "period_key": period_key, "metric": reservation.metric},
        )
    reservation.amount_used = used
    reservation.state = "committed" if actual is not None else "released"
    reservation.resolved_at = utcnow()
    session.flush()
    return reservation


def commit(session: Session, reservation_id: uuid.UUID, actual_amount: float) -> UsageReservation:
    """Replace the reservation by the measured consumption (which may exceed it: it is recorded, never hidden)."""
    return _settle(session, reservation_id, actual_amount)


def release(session: Session, reservation_id: uuid.UUID) -> UsageReservation:
    """Give the reservation back (the call failed or was cancelled before it consumed anything)."""
    return _settle(session, reservation_id, None)


def snapshot(session: Session, settings: Settings, learner_id: uuid.UUID) -> dict:
    today = _today()
    result: dict[str, dict[str, dict[str, float]]] = {}
    for metric in METRICS:
        daily_limit, total_limit = limits_for(settings, metric)
        result[metric] = {}
        for scope, period_key, limit_value in (("daily", today, daily_limit), ("total", TOTAL_PERIOD_KEY, total_limit)):
            counter = session.scalar(
                select(UsageCounter).where(
                    UsageCounter.learner_id == learner_id, UsageCounter.scope == scope,
                    UsageCounter.period_key == period_key, UsageCounter.metric == metric,
                )
            )
            used = float(counter.used) if counter else 0.0
            reserved = float(counter.reserved) if counter else 0.0
            result[metric][scope] = {
                "used": used, "reserved": reserved, "limit": float(limit_value),
                "remaining": float(limit_value) - used - reserved,
            }
    prices = session.scalars(select(PricingEntry)).all()
    return {
        "period": today.isoformat(),
        "counters": result,
        "pricing_table_entries": len(prices),
        "estimated_cost": None if not prices else _estimate(result, prices),
        "note": "pricing table is empty until Phase B records the authorised allowance" if not prices else "",
    }


def _estimate(counters: dict, prices: list[PricingEntry]) -> dict:
    total = 0.0
    currency = prices[0].currency
    for entry in prices:
        used = counters.get(entry.metric, {}).get("total", {}).get("used", 0.0)
        total += used * float(entry.unit_price)
    return {"amount": round(total, 4), "currency": currency}
