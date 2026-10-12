"""The learner's day. Points, streaks and goals count by the calendar in Brussels, where the course is set;
usage allowances keep their UTC day (see docs/ENGINEERING.md, usage counters)."""
from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

LEARNER_TIMEZONE = ZoneInfo("Europe/Brussels")


def local_today(now: datetime | None = None) -> date:
    """The Brussels calendar day of `now` (the current moment when left out); `now` must be timezone-aware."""
    return (now or datetime.now(UTC)).astimezone(LEARNER_TIMEZONE).date()


def day_bounds_utc(now: datetime | None = None) -> tuple[datetime, datetime]:
    """The start and the end of the Brussels day of `now`, in UTC (23 or 25 hours apart on a clock change)."""
    day = local_today(now)
    start = datetime.combine(day, time.min, tzinfo=LEARNER_TIMEZONE)
    end = datetime.combine(day + timedelta(days=1), time.min, tzinfo=LEARNER_TIMEZONE)
    return start.astimezone(UTC), end.astimezone(UTC)
