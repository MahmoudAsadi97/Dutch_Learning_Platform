"""Record what a learner did and award its points: one append-only event per countable action, then the day.

Every award goes through `record_activity`. The event row is inserted first with ON CONFLICT DO NOTHING on
(learner_id, kind, dedupe_key), so a retried or concurrent request finds the row and awards nothing; only a new
event moves `learning_days`. A day's points therefore equal the sum of its events (days from before the events
table carry one backfilled `legacy` event). The streak and the goal read `learning_days`.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from dlp.db.base import utcnow
from dlp.domains.activity.day import local_today
from dlp.domains.activity.models import ActivityEvent, LearningDay
from dlp.domains.activity.rules import COUNTERS, RULES, SKILLS, Rule
from dlp.domains.profile.models import LearnerProfile

DAILY_GOAL = 20


@dataclass(frozen=True)
class Award:
    points: int
    recorded: bool  # False when the same action had already been recorded; nothing was awarded
    goal_reached: bool = False  # this award took the day from below its goal to the goal or past it


def reached(*awards: Award | None) -> dict[str, bool]:
    """`{"goal_reached": True}` for an action response when one of its awards crossed the day's goal, so the
    screen that earned it can mark the moment; empty otherwise."""
    return {"goal_reached": True} if any(award and award.goal_reached for award in awards) else {}


def replayed(session: Session, learner_id: uuid.UUID, request_id: str) -> dict[str, bool]:
    """What `reached` said the first time, for a request that is answered again from its stored result: the
    response that crossed the goal may never have arrived. Only today's crossing is repeated."""
    if not request_id:
        return {}
    crossed = session.scalar(select(ActivityEvent.id).where(
        ActivityEvent.learner_id == learner_id, ActivityEvent.request_id == request_id,
        ActivityEvent.day == local_today(), ActivityEvent.meta["goal_reached"].as_boolean().is_(True),
    ).limit(1))
    return {"goal_reached": True} if crossed else {}


def goal_for(session: Session, learner_id: uuid.UUID) -> int:
    """The learner's daily goal from the profile; the default before a profile exists."""
    goal = session.scalar(select(LearnerProfile.daily_goal_points).where(LearnerProfile.learner_id == learner_id))
    return goal or DAILY_GOAL


def dedupe_key(rule: Rule, ref: str, *, request_id: str, day: date) -> str:
    if rule.scope == "once":
        return ref
    if rule.scope == "per_day":
        return f"{day.isoformat()}:{ref}"
    if not request_id:
        raise ValueError("an activity counted per request needs the request id")
    return f"{ref}:{request_id}"


def record_activity(session: Session, learner_id: uuid.UUID, *, kind: str, ref: str, request_id: str = "",
                    units: int = 1, counted: int | None = None, skill: str | None = None,
                    meta: dict[str, Any] | None = None, now: datetime | None = None) -> Award:
    """Record one action of `kind` on `ref` (an episode id, a word id, ...) and award what the rules say.

    `units` multiplies the points (the number of answered questions, for example) and moves the day counter,
    unless `counted` gives the counter its own number (the correct ones among them). `skill` is the action's own
    skill when the rule leaves it open or the action decides it (a typed turn is writing). An action with no units
    is still recorded, so it cannot be replayed later for points."""
    rule = RULES[kind]
    if units < 0 or (counted is not None and counted < 0):
        raise ValueError("units cannot be negative")
    if skill is not None and skill not in SKILLS:
        raise ValueError(f"unknown skill: {skill}")
    day = local_today(now)
    points = rule.points * units
    count = units if counted is None else counted
    event_id = session.scalar(
        insert(ActivityEvent).values(
            id=uuid.uuid4(), learner_id=learner_id, kind=kind, ref=ref,
            dedupe_key=dedupe_key(rule, ref, request_id=request_id, day=day), day=day, points=points, units=units,
            skill=skill or rule.skill, request_id=request_id, meta=meta or {}, created_at=utcnow(),
        ).on_conflict_do_nothing(index_elements=["learner_id", "kind", "dedupe_key"]).returning(ActivityEvent.id)
    )
    if event_id is None:
        return Award(points=0, recorded=False)
    if not (points or (rule.counter and count)):
        return Award(points=0, recorded=True)
    row = add_to_day(session, learner_id, day=day, points=points, counts={rule.counter: count} if rule.counter else {})
    goal = row.goal_target or DAILY_GOAL
    goal_reached = 0 < points and row.points - points < goal <= row.points
    if goal_reached:
        # kept with the event, so a retry of the same request can still say so (`replayed`)
        session.execute(update(ActivityEvent).where(ActivityEvent.id == event_id)
                        .values(meta={**(meta or {}), "goal_reached": True}))
    return Award(points=points, recorded=True, goal_reached=goal_reached)


def add_to_day(session: Session, learner_id: uuid.UUID, *, day: date, points: int,
               counts: dict[str, int] | None = None) -> LearningDay:
    """Add points and counter units to one learner day. Learner actions come here through `record_activity`;
    calling it directly (seeding history in tests) adds points that no event explains."""
    counts = counts or {}
    unknown = sorted(set(counts) - set(COUNTERS))
    if unknown:
        raise ValueError(f"unknown day counters: {unknown}")
    goal = goal_for(session, learner_id)
    values = {name: counts.get(name, 0) for name in COUNTERS}
    statement = insert(LearningDay).values(
        id=uuid.uuid4(), learner_id=learner_id, day=day, points=points, goal_target=goal, goal_met=points >= goal,
        updated_at=utcnow(), **values,
    ).on_conflict_do_update(
        index_elements=["learner_id", "day"],
        set_={
            "points": LearningDay.points + points,
            **{name: getattr(LearningDay, name) + values[name] for name in COUNTERS},
            # the goal in force at the day's latest activity; once the day is over it stays as it was
            "goal_target": goal,
            "goal_met": (LearningDay.points + points) >= goal,
            "updated_at": utcnow(),
        },
    )
    session.execute(statement)
    row = session.scalar(select(LearningDay).where(LearningDay.learner_id == learner_id, LearningDay.day == day)
                         .execution_options(populate_existing=True))
    assert row is not None
    return row


def retarget_today(session: Session, learner_id: uuid.UUID, goal: int) -> None:
    """A new daily goal applies to today at once, so the dot today leaves behind is the goal Today showed."""
    session.execute(update(LearningDay).where(LearningDay.learner_id == learner_id, LearningDay.day == local_today())
                    .values(goal_target=goal, goal_met=LearningDay.points >= goal, updated_at=utcnow()))


def streak(session: Session, learner_id: uuid.UUID, today_date: date | None = None) -> dict:
    """Consecutive active days ending today or yesterday. A missed day resets; nothing is bought back (O9)."""
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
    goal = goal_for(session, learner_id)
    rows = {row.day: row for row in session.scalars(select(LearningDay).where(
        LearningDay.learner_id == learner_id, LearningDay.day >= start, LearningDay.day <= end))}
    out = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        row = rows.get(day)
        out.append({"day": day.isoformat(), "points": row.points if row else 0,
                    # past days keep the goal they were played against; today follows the current goal
                    "goal_met": bool(row and (row.goal_met if day < end else row.points >= goal))})
    return out


def events(session: Session, learner_id: uuid.UUID) -> list[dict]:
    """Every recorded action of the learner, oldest first, for the owner export."""
    rows = session.scalars(select(ActivityEvent).where(ActivityEvent.learner_id == learner_id)
                           .order_by(ActivityEvent.created_at, ActivityEvent.id))
    return [{"kind": row.kind, "ref": row.ref, "day": row.day.isoformat(), "points": row.points, "units": row.units,
             "skill": row.skill, "request_id": row.request_id, "meta": row.meta,
             "created_at": row.created_at.isoformat()} for row in rows]
