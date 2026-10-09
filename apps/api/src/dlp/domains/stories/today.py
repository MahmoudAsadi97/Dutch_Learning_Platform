"""The day, the streak and the goal, as the story code and its tests have always imported them.

They live in the activity domain now (`dlp.domains.activity`); awards go through `record_activity`. This
module keeps the old names, and `add_points` only for seeding history in tests.
"""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.orm import Session

from dlp.domains.activity.day import LEARNER_TIMEZONE, local_today
from dlp.domains.activity.models import LearningDay
from dlp.domains.activity.service import DAILY_GOAL, add_to_day, goal_for, recent_days, streak

__all__ = ["DAILY_GOAL", "LEARNER_TIMEZONE", "add_points", "goal_for", "local_today", "recent_days", "streak"]


def add_points(session: Session, learner_id: uuid.UUID, *, points: int, day: date | None = None,
               **counts: int) -> LearningDay:
    """Seed a day directly (tests); learner actions earn points through `activity.service.record_activity`."""
    return add_to_day(session, learner_id, day=day or local_today(), points=points, counts=counts)
