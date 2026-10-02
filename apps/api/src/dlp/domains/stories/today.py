"""Daily points, the streak and the goal. Points reward doing, never a score about the learner's Dutch."""
from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from dlp.db.base import utcnow
from dlp.domains.stories.models import LearningDay

LEARNER_TIMEZONE = ZoneInfo("Europe/Brussels")
DAILY_GOAL = 20


def local_today(now: datetime | None = None) -> date:
    return (now or datetime.now(UTC)).astimezone(LEARNER_TIMEZONE).date()


def add_points(session: Session, learner_id: uuid.UUID, *, points: int, episodes_read: int = 0,
               words_reviewed: int = 0, questions_correct: int = 0, read_aloud: int = 0,
               day: date | None = None) -> LearningDay:
    day = day or local_today()
    statement = insert(LearningDay).values(
        id=uuid.uuid4(), learner_id=learner_id, day=day, points=points, episodes_read=episodes_read,
        words_reviewed=words_reviewed, questions_correct=questions_correct, read_aloud=read_aloud,
        goal_met=points >= DAILY_GOAL, updated_at=utcnow(),
    ).on_conflict_do_update(
        index_elements=["learner_id", "day"],
        set_={
            "points": LearningDay.points + points,
            "episodes_read": LearningDay.episodes_read + episodes_read,
            "words_reviewed": LearningDay.words_reviewed + words_reviewed,
            "questions_correct": LearningDay.questions_correct + questions_correct,
            "read_aloud": LearningDay.read_aloud + read_aloud,
            "goal_met": (LearningDay.points + points) >= DAILY_GOAL,
            "updated_at": utcnow(),
        },
    )
    session.execute(statement)
    row = session.scalar(select(LearningDay).where(LearningDay.learner_id == learner_id, LearningDay.day == day)
                         .execution_options(populate_existing=True))
    assert row is not None
    return row


def streak(session: Session, learner_id: uuid.UUID, today_date: date | None = None) -> dict:
    """Consecutive active days ending today or yesterday. A missed day resets; nothing is bought back."""
    today_date = today_date or local_today()
    rows = list(session.scalars(select(LearningDay).where(LearningDay.learner_id == learner_id, LearningDay.points > 0)
                                .order_by(LearningDay.day.desc()).limit(400)))
    active = [row.day for row in rows]
    current = 0
    cursor = today_date if today_date in active else today_date - timedelta(days=1)
    active_set = set(active)
    while cursor in active_set:
        current += 1
        cursor -= timedelta(days=1)
    best = run = 0
    previous: date | None = None
    for day in sorted(active):
        run = run + 1 if previous is not None and day - previous == timedelta(days=1) else 1
        best = max(best, run)
        previous = day
    today_row = next((row for row in rows if row.day == today_date), None)
    return {"current": current, "best": best, "today_active": today_date in active_set,
            "today_points": today_row.points if today_row else 0, "active_days": len(active)}


def recent_days(session: Session, learner_id: uuid.UUID, days: int = 14) -> list[dict]:
    end = local_today()
    start = end - timedelta(days=days - 1)
    rows = {row.day: row for row in session.scalars(select(LearningDay).where(
        LearningDay.learner_id == learner_id, LearningDay.day >= start, LearningDay.day <= end))}
    out = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        row = rows.get(day)
        out.append({"day": day.isoformat(), "points": row.points if row else 0,
                    "goal_met": bool(row and row.points >= DAILY_GOAL)})
    return out
