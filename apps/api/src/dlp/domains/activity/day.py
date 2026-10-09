"""The learner's day. Points, streaks and goals count by the calendar in Brussels, where the course is set;
usage allowances keep their UTC day (see docs/ENGINEERING.md, usage counters)."""
from __future__ import annotations

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

LEARNER_TIMEZONE = ZoneInfo("Europe/Brussels")


def local_today(now: datetime | None = None) -> date:
    """The Brussels calendar day of `now` (the current moment when left out); `now` must be timezone-aware."""
    return (now or datetime.now(UTC)).astimezone(LEARNER_TIMEZONE).date()
