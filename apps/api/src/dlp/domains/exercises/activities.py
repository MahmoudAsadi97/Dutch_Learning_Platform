"""Topic and lesson sessions (roadmap 3.8): a practice topic or a stage lesson as a session.

Reading or listening: one passage step (the text to read, or the topic's or lesson's listening, heard part by
part from its own /listening route), then the activity's authored questions in their order, each a choice with
its options shuffled under opaque ids. The passage's translation, or the listening transcript, is shown once
every question has been answered. Only the first attempt at each question counts towards the activity, at
finish, through the unchanged `objective_result` (75 %: both of a topic's two questions, all three of a
lesson's); a question skipped the first time counts as answered wrong, and a session finished with a question
never tried counts for nothing. A retry session asks only the questions the last finished session on the same
activity missed the first time; it is practice and completes nothing.

Speaking or writing (topics only): a warm-up on the topic's own words, built by `plan()`; it never completes
anything. The open task, and its completion, stay with POST /curriculum/{stage}/topics/{topic}/practice.

A lesson is read from `stage.lesson` alone; the final check (`stage.test`) is never a source.
"""
from __future__ import annotations

import hashlib
import random
import uuid
from dataclasses import dataclass
from typing import Any, Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from dlp.domains.curriculum import service as curriculum
from dlp.domains.curriculum import topics
from dlp.domains.curriculum.library import library_for
from dlp.domains.curriculum.models import CurriculumPractice, TopicPractice
from dlp.domains.curriculum.schemas import STAGE_IDS, Localized, Question
from dlp.domains.exercises.generators import Draft, authored_choice
from dlp.errors import DomainError

# the passage steps: read or listened to, then closed with done; never graded, never a point
PASSAGE_KINDS = frozenset({"read_passage", "listen_passage"})
RECEPTIVE = ("reading", "listening")
WARM_UP_SIZE = 6


class ActivityNotFound(DomainError):
    code = "exercise"

    def __init__(self, detail: str) -> None:
        super().__init__(detail, 404)


@dataclass(frozen=True)
class Activity:
    """What a topic or lesson session is built from, and what its result is checked against at finish."""
    scope: Literal["topic", "lesson"]
    stage_id: str
    skill: str
    content_version: str  # the topic's own hash (as TopicPractice stores it), or the lesson's
    bank: topics.TopicBank | None = None
    topic: topics.PracticeTopic | None = None
    text: Localized | None = None  # the reading text or the listening transcript
    questions: tuple[Question, ...] = ()

    @property
    def topic_id(self) -> str:
        return self.topic.id if self.topic else ""


def _version(model: Any) -> str:
    return hashlib.sha256(model.model_dump_json().encode()).hexdigest()


def stage_of(topic_id: str) -> str:
    """Read the stage prefix; an authored slug may itself contain ``-t``."""
    for stage_id in STAGE_IDS:
        if topic_id.startswith(f"{stage_id}-t"):
            return stage_id
    raise ActivityNotFound("practice topic not found")


def activity_for(stage_id: str, *, topic_id: str | None, skill: str) -> Activity:
    """The topic (by id, at its own stage) or the stage's lesson, for one skill. Banks are read through the
    module, so a test's bank replaces the real one."""
    try:
        if topic_id is not None:
            bank = topics.topics_for(stage_id)
            topic = topics.topic_for(bank, topic_id)
            activity = getattr(topic, skill)
            receptive = skill in RECEPTIVE
            return Activity(scope="topic", stage_id=stage_id, skill=skill, content_version=_version(topic),
                            bank=bank, topic=topic, text=activity.text if receptive else None,
                            questions=tuple(activity.questions) if receptive else ())
        lesson = curriculum.stage_for(stage_id).lesson  # the lesson only: the final check is never a source
    except curriculum.CurriculumError as missing:
        raise ActivityNotFound("practice topic not found" if topic_id else "learning stage not found") from missing
    if skill == "reading":
        text, questions = lesson.story, lesson.reading_questions
    else:
        text, questions = lesson.listening, lesson.listening_questions
    return Activity(scope="lesson", stage_id=stage_id, skill=skill, content_version=_version(lesson), text=text,
                    questions=tuple(questions))


def question_ref(activity: Activity, question: Question) -> str:
    """A topic's question ids are unique across the course; a lesson's repeat from stage to stage (r1, l1)."""
    return f"question:{question.id}" if activity.scope == "topic" else f"question:{activity.stage_id}:{question.id}"


def _vocabulary(activity: Activity) -> list[dict[str, Any]]:
    """The topic's own words with their meaning, as the classic topic page shows them beside the passage."""
    if activity.topic is None:
        return []
    words = {word.id: word for word in library_for(activity.stage_id).vocabulary}
    return [{"term": words[key].term, "meaning": {"en": words[key].meaning.en, "fa": words[key].meaning.fa}}
            for key in activity.topic.vocabulary_ids if key in words]


def passage(activity: Activity) -> Draft:
    """The passage step. The prompt holds the Dutch only; the translation or transcript (the key's `reveal`)
    joins it in the session view once every question is answered."""
    if activity.text is None:
        raise ValueError("only a reading or listening activity has a passage")
    if activity.skill == "reading":
        prompt: dict[str, Any] = {"kind": "read_passage", "text": {"nl": activity.text.nl}}
    else:
        prompt = {"kind": "listen_passage", "parts": len(curriculum.audio_parts(activity.text.nl))}
    owner = activity.topic_id or f"{activity.stage_id}:lesson"
    return Draft(kind=prompt["kind"], ref=f"passage:{owner}:{activity.skill}", skill=activity.skill,
                 prompt={**prompt, "vocabulary": _vocabulary(activity)},
                 key={"reveal": activity.text.model_dump()})


def comprehension(activity: Activity, rng: random.Random, *, only: set[str] | None = None) -> list[Draft]:
    """The passage, then the authored questions (all of them, or `only` those of a retry) in their order."""
    questions = [question for question in activity.questions if only is None or question.id in only]
    return [passage(activity), *(authored_choice(question, rng, skill=activity.skill,
                                                 ref=question_ref(activity, question))
                                 for question in questions)]


def _checked(activity: Activity, chosen: dict[str, int | None]) -> tuple[dict[str, Any], dict[str, int]]:
    """The course's own check over the first answers (question id to the original option index, None when the
    first try was a skip): a skip counts as answered wrong. Returns the result and the answers as given."""
    answered = {qid: index for qid, index in chosen.items() if index is not None}
    filled = {question.id: answered.get(question.id, (question.answer_index + 1) % len(question.options))
              for question in activity.questions}
    return curriculum.objective_result(list(activity.questions), filled), answered


def record_result(session: Session, *, learner_id: uuid.UUID, session_id: uuid.UUID, activity: Activity,
                  chosen: dict[str, int | None]) -> dict[str, Any]:
    """The course's check over a session's first answers, recorded as the classic form records it: a topic's
    sticky completion and the stage skill (`_persist_topic_result`) with one practice observation, or a lesson's
    stage skill (`_persist_core_practice`, no observation, as before). The evidence holds the answers given,
    never an answer key."""
    result, answered = _checked(activity, chosen)
    evidence = {"answers": answered, "skipped": sorted(qid for qid, index in chosen.items() if index is None),
                "result": result.copy(), "session_id": str(session_id)}
    if activity.topic is not None:
        completed = _record_topic(session, learner_id=learner_id, session_id=session_id, activity=activity,
                                  result=result, answered=answered, evidence=evidence)
    else:
        completed = curriculum._persist_core_practice(session, learner_id=learner_id, stage_id=activity.stage_id,
                                                      skill=activity.skill, completed=result["passed"],
                                                      evidence=evidence)
    return {"counted": True, "reason": None, "passed": result["passed"], "correct": result["correct"],
            "total": result["total"], "required": result["required"], "completed": completed}


def _record_topic(session: Session, *, learner_id: uuid.UUID, session_id: uuid.UUID, activity: Activity,
                  result: dict[str, Any], answered: dict[str, int], evidence: dict[str, Any]) -> bool:
    # imported here, as topics.save_topic_practice does: coaching reads the curriculum when it is imported
    from dlp.domains.coaching.service import record_observation

    if activity.topic is None or activity.bank is None:
        raise ValueError("only a topic is recorded with an observation")
    version, completed = topics._persist_topic_result(
        session, learner_id=learner_id, bank=activity.bank, topic=activity.topic, skill=activity.skill,
        completed=result["passed"], passed=result["passed"], evidence=evidence)
    failed = [question.id for question in activity.questions if answered.get(question.id) != question.answer_index]
    # one observation per session; its id is never a client's (a client's request id has no colon)
    record_observation(session, learner_id=learner_id, stage_id=activity.stage_id, topic_id=activity.topic.id,
                       skill=activity.skill, source="topic_practice", request_id=f"exercise:{session_id}",
                       content_version=version, passed=result["passed"],
                       summary={"correct": result["correct"], "total": result["total"], "assessed": True},
                       failed_refs=failed,
                       payload={"stage_id": activity.stage_id, "topic_id": activity.topic.id,
                                "skill": activity.skill, "answers": answered, "session_id": str(session_id)},
                       response={"passed": result["passed"], "correct": result["correct"],
                                 "total": result["total"], "completed": completed, "skill": activity.skill})
    return completed


def stored_completion(session: Session, *, learner_id: uuid.UUID, stage_id: str, topic_id: str, skill: str) -> bool:
    """Whether the topic (a lesson: the stage skill) is completed, whatever completed it."""
    if topic_id:
        query = select(TopicPractice.completed).where(
            TopicPractice.learner_id == learner_id, TopicPractice.stage_id == stage_id,
            TopicPractice.topic_id == topic_id, TopicPractice.skill == skill)
    else:
        query = select(CurriculumPractice.completed).where(
            CurriculumPractice.learner_id == learner_id, CurriculumPractice.stage_id == stage_id,
            CurriculumPractice.skill == skill)
    return bool(session.scalar(query))
