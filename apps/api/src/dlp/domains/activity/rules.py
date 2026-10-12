"""What each kind of activity earns, which day counter it moves and how often it may count.

One table for every kind, so point values are tuned in one place. Points reward doing something, never a
judgement of the learner's Dutch (D-19, revised in D-27 and D-34): every kind of practice earns them, for what code
can observe (submitted, inside the word limits, a turn stored), never for a model's verdict.

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
    points: int  # per unit (one answered question, one reviewed word, ...)
    counter: str | None  # the learning_days column the units are added to
    skill: str | None  # reading, listening, speaking or writing; None when the action trains no single skill
    scope: Scope


# The skills an action may train; an action's own skill (a typed turn is writing, a spoken one speaking) may
# replace its rule's.
SKILLS = ("reading", "listening", "speaking", "writing")

RULES: dict[str, Rule] = {
    "episode_read": Rule(points=10, counter="episodes_read", skill="reading", scope="once"),
    # per answered question (O1); the day counts the correct ones in questions_correct
    "episode_questions": Rule(points=3, counter="questions_correct", skill="reading", scope="once"),
    "episode_choice": Rule(points=2, counter=None, skill="reading", scope="once"),
    "read_aloud": Rule(points=5, counter="read_aloud", skill="speaking", scope="once"),
    "word_review": Rule(points=1, counter="words_reviewed", skill=None, scope="per_request"),
    "video_watched": Rule(points=10, counter="videos_watched", skill="listening", scope="once"),
    "video_questions": Rule(points=3, counter="questions_correct", skill="listening", scope="once"),
    # an exercise item that closed after a real answer, right or wrong; a session with five closed items
    "exercise_item": Rule(points=1, counter="exercise_items", skill=None, scope="once"),
    "exercise_session": Rule(points=5, counter="exercise_sessions", skill=None, scope="once"),
    # Course forms (a stage lesson's or a topic's classic form): per question answered, or the open task once, per
    # activity and day; an exercise session pays its items instead and never these (D-31). The skill is the
    # activity's.
    "course_questions": Rule(points=1, counter=None, skill=None, scope="per_day"),
    "course_task": Rule(points=5, counter=None, skill=None, scope="per_day"),
    # a submitted stage check, passed or not, once per attempt
    "stage_check": Rule(points=15, counter=None, skill=None, scope="once"),
    # missions: a reading or listening step once answered (per question), the written message, each stored turn
    "mission_questions": Rule(points=1, counter=None, skill=None, scope="once"),
    "mission_writing": Rule(points=5, counter=None, skill="writing", scope="once"),
    "mission_turn": Rule(points=2, counter=None, skill=None, scope="once"),
    # a topic conversation's answer turn (help turns earn nothing)
    "conversation_turn": Rule(points=2, counter=None, skill=None, scope="once"),
    # the microphone warm-up with recognised speech, once a day (the client says it is one, so it stays small)
    "speech_warmup": Rule(points=2, counter=None, skill="speaking", scope="per_day"),
}
