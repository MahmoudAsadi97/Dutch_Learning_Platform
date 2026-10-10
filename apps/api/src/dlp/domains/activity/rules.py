"""What each kind of activity earns, which day counter it moves and how often it may count.

One table for every kind, so point values are tuned in one place. Points reward doing something, never a
judgement of the learner's Dutch (D-19, revised in D-27).

`scope` decides when the same action counts again:
- once: once per `ref` for good (reading episode 12, the questions of video 3);
- per_day: once per `ref` per Brussels day;
- per_request: once per `ref` and request id, so a retried request never pays twice but a new action does.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Scope = Literal["once", "per_day", "per_request"]

# the learning_days columns an activity may move; anything else is a typo in the table below
COUNTERS = ("episodes_read", "words_reviewed", "questions_correct", "read_aloud", "videos_watched",
            "exercise_items", "exercise_sessions")


@dataclass(frozen=True)
class Rule:
    points: int  # per unit (one correct question, one reviewed word, ...)
    counter: str | None  # the learning_days column the units are added to
    skill: str | None  # reading, listening, speaking or writing; None when the action trains no single skill
    scope: Scope


RULES: dict[str, Rule] = {
    "episode_read": Rule(points=10, counter="episodes_read", skill="reading", scope="once"),
    "episode_questions": Rule(points=3, counter="questions_correct", skill="reading", scope="once"),
    "episode_choice": Rule(points=2, counter=None, skill="reading", scope="once"),
    "read_aloud": Rule(points=5, counter="read_aloud", skill="speaking", scope="once"),
    "word_review": Rule(points=1, counter="words_reviewed", skill=None, scope="per_request"),
    "video_watched": Rule(points=10, counter="videos_watched", skill="listening", scope="once"),
    "video_questions": Rule(points=3, counter="questions_correct", skill="listening", scope="once"),
    # an exercise item that closed after a real answer, right or wrong; a session with five closed items
    "exercise_item": Rule(points=1, counter="exercise_items", skill=None, scope="once"),
    "exercise_session": Rule(points=5, counter="exercise_sessions", skill=None, scope="once"),
}
