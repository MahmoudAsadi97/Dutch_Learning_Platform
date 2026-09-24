"""Four-skill topic banks and learner-owned practice; browsing never awards completion."""
from __future__ import annotations

import hashlib
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from dlp.config import CONTENT_DIR, Settings
from dlp.db.base import utcnow
from dlp.domains.curriculum import service
from dlp.domains.curriculum.library import library_for, normalise
from dlp.domains.curriculum.models import CurriculumPractice, TopicPractice
from dlp.domains.curriculum.schemas import SKILLS, STAGE_IDS, Localized, Question, Skill, Task
from dlp.providers.registry import Providers


class ReceptiveActivity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: Localized
    questions: list[Question] = Field(min_length=2, max_length=12)


class PracticeTopic(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=60, pattern=r"^[a-z0-9-]+$")
    title: Localized
    category: Localized
    objectives: list[Localized] = Field(min_length=1, max_length=6)
    language_focus: Localized
    vocabulary_ids: list[str] = Field(min_length=1, max_length=12)
    reading: ReceptiveActivity
    listening: ReceptiveActivity
    speaking: Task
    writing: Task

    @model_validator(mode="after")
    def valid_activities(self):
        if normalise(self.reading.text.nl) == normalise(self.listening.text.nl):
            raise ValueError("listening needs a distinct source, not the reading text")
        for skill in ("reading", "listening"):
            activity = getattr(self, skill)
            if len(service.audio_parts(activity.text.nl)) > 101:
                raise ValueError("activity exceeds the supported bounded listening parts")
            for question in activity.questions:
                if not question.id.startswith(self.id + "-"):
                    raise ValueError("question ID must belong to its own topic")
                for language in ("nl", "en", "fa"):
                    options = [normalise(getattr(item, language)) for item in question.options]
                    if len(set(options)) != len(options):
                        raise ValueError("question options must be distinct in every support language")
        for skill in ("speaking", "writing"):
            task = getattr(self, skill)
            count = service.word_count(task.sample.nl)
            if task.sample_is_excerpt:
                if skill != "writing" or not 5 <= count < task.min_words:
                    raise ValueError("only writing may have an explicitly shorter sample excerpt")
            elif not task.min_words <= count <= task.max_words:
                raise ValueError("task sample must meet its stated word range")
        if self.speaking.max_words > 100:
            raise ValueError("speaking practice must fit the bounded recording journey")
        if len(set(self.vocabulary_ids)) != len(self.vocabulary_ids):
            raise ValueError("repeated topic vocabulary reference")
        return self


class TopicBank(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1]
    stage_id: str
    review_status: Literal["unreviewed"]
    topics: list[PracticeTopic] = Field(min_length=100)

    @model_validator(mode="after")
    def consistent_bank(self):
        if self.stage_id not in STAGE_IDS:
            raise ValueError("unknown topic stage")
        ids = [topic.id for topic in self.topics]
        if len(set(ids)) != len(ids) or any(not key.startswith(f"{self.stage_id}-t") for key in ids):
            raise ValueError("topic IDs must be unique and bound to their stage")
        values = [normalise(topic.title.nl) for topic in self.topics]
        if len(set(values)) != len(values):
            raise ValueError("topics require different communicative situation titles")
        for skill in SKILLS:
            values = [normalise(getattr(topic, skill).text.nl if skill in ("reading", "listening")
                                else getattr(topic, skill).prompt.nl) for topic in self.topics]
            if len(set(values)) != len(values):
                raise ValueError(f"duplicate {skill} activities in this stage")
        question_ids = [q.id for topic in self.topics for skill in ("reading", "listening")
                        for q in getattr(topic, skill).questions]
        if len(set(question_ids)) != len(question_ids):
            raise ValueError("question IDs must be unique across topics and skills")
        # Recursive validation covers the existing localized Task/Question types, including criteria.
        def check_copy(value):
            if isinstance(value, dict):
                if "nl" in value and not all(str(value.get(lang, "")).strip() for lang in ("nl", "en", "fa")):
                    raise ValueError("every learning string needs nonblank Dutch, English and Persian")
                for child in value.values():
                    check_copy(child)
            elif isinstance(value, list):
                for child in value:
                    check_copy(child)
        check_copy(self.model_dump())
        return self


@lru_cache(maxsize=16)
def _read(path: str, modified: int) -> TopicBank:
    return TopicBank.model_validate_json(Path(path).read_text(encoding="utf-8"))


def topics_for(stage_id: str) -> TopicBank:
    if stage_id not in STAGE_IDS:
        raise service.CurriculumError("learning stage not found", 404)
    path = CONTENT_DIR / "practice" / f"{stage_id}.json"
    bank = _read(str(path), path.stat().st_mtime_ns)
    if bank.stage_id != stage_id:
        raise ValueError("topic file does not match its requested stage")
    known = {word.id for word in library_for(stage_id).vocabulary}
    if any(not set(topic.vocabulary_ids).issubset(known) for topic in bank.topics):
        raise ValueError("topic refers to vocabulary outside this stage library")
    return bank


def validate_all_topics() -> list[TopicBank]:
    return [topics_for(stage_id) for stage_id in STAGE_IDS]


def topic_for(bank: TopicBank, topic_id: str) -> PracticeTopic:
    topic = next((item for item in bank.topics if item.id == topic_id), None)
    if topic is None:
        raise service.CurriculumError("practice topic not found", 404)
    return topic


def _progress(session: Session, learner_id: uuid.UUID, stage_id: str, skill: Skill) -> dict[str, TopicPractice]:
    return {item.topic_id: item for item in session.scalars(select(TopicPractice).where(
        TopicPractice.learner_id == learner_id, TopicPractice.stage_id == stage_id, TopicPractice.skill == skill,
    ))}


def topic_page(session: Session, learner_id: uuid.UUID, bank: TopicBank, *, skill: Skill, query: str = "",
               category: str = "", status: str = "all", offset: int = 0, limit: int = 12) -> dict:
    saved = _progress(session, learner_id, bank.stage_id, skill)
    labels = {topic.category.nl: topic.category.model_dump() for topic in bank.topics}
    def matches(topic):
        progress = saved.get(topic.id)
        complete = bool(progress and progress.completed)
        if category and topic.category.nl != category:
            return False
        if status == "completed" and not complete or status == "not_started" and progress:
            return False
        terms = [getattr(copy, lang) for copy in (topic.title, topic.category, topic.language_focus, *topic.objectives)
                 for lang in ("nl", "en", "fa")]
        return not query or normalise(query) in normalise(" ".join(terms))
    selected = [topic for topic in bank.topics if matches(topic)]
    return {
        "stage_id": bank.stage_id, "skill": skill, "total": len(selected), "total_topics": len(bank.topics),
        "offset": offset, "limit": limit, "completed_count": sum(bool(saved.get(t.id) and saved[t.id].completed)
                                                                   for t in bank.topics),
        "categories": [labels[key] for key in sorted(labels)], "learner_key": str(learner_id),
        "items": [{"id": topic.id, "title": topic.title.model_dump(), "category": topic.category.model_dump(),
                   "completed": bool(saved.get(topic.id) and saved[topic.id].completed), "attempted": topic.id in saved}
                  for topic in selected[offset:offset + limit]],
    }


def topic_detail(session: Session, learner_id: uuid.UUID, bank: TopicBank, topic: PracticeTopic, *, skill: Skill,
                 recording_max_seconds: float = 60) -> dict:
    activity = getattr(topic, skill).model_dump()
    if skill in ("reading", "listening"):
        for question in activity["questions"]:
            question.pop("answer_index")
            question.pop("explanation")
        if skill == "listening":
            activity["audio_parts"] = len(service.audio_parts(topic.listening.text.nl))
    saved = _progress(session, learner_id, bank.stage_id, skill).get(topic.id)
    words = {word.id: word for word in library_for(bank.stage_id).vocabulary}
    return {
        "stage_id": bank.stage_id, "skill": skill, "id": topic.id, "title": topic.title.model_dump(),
        "category": topic.category.model_dump(), "objectives": [item.model_dump() for item in topic.objectives],
        "language_focus": topic.language_focus.model_dump(), "review_status": bank.review_status,
        "vocabulary": [words[key].model_dump(exclude={"topic"}) for key in topic.vocabulary_ids],
        "activity": activity,
        **({"context": {"reading": topic.reading.text.model_dump(), "listening": topic.listening.text.model_dump()}}
           if skill in ("speaking", "writing") else {}),
        "progress": {"completed": bool(saved and saved.completed), "attempted": saved is not None},
        "policy": {"recording_max_seconds": min(60, recording_max_seconds)},
    }


def save_topic_practice(session: Session, settings: Settings, providers: Providers, *, learner_id: uuid.UUID,
                        bank: TopicBank, topic: PracticeTopic, skill: Skill, answers: dict[str, int], text: str,
                        asset_id: uuid.UUID | None, request_id: str) -> dict:
    if skill in ("reading", "listening"):
        if text or asset_id:
            raise service.CurriculumError("this skill accepts answers to its own questions only", 422)
        questions = getattr(topic, skill).questions
        result = service.objective_result(questions, answers)
        completed = result["passed"]
        evidence = {"answers": answers, "result": result.copy()}
        result["explanations"] = [{"id": q.id, "correct": answers[q.id] == q.answer_index,
                                   "answer_index": q.answer_index, "explanation": q.explanation.model_dump()}
                                  for q in questions]
    else:
        if answers or skill == "writing" and asset_id:
            raise service.CurriculumError("this skill requires its own written or spoken response", 422)
        task = getattr(topic, skill)
        if skill == "speaking":
            if asset_id is None:
                raise service.CurriculumError("record your spoken answer first", 422)
            # The server-owned transcript, never a client-supplied substitute, is assessed.
            asset = service.recording(session, learner_id, asset_id)
            if asset.duration_seconds > min(60, settings.max_audio_seconds):
                raise service.CurriculumError("record a response within this activity's time limit", 422)
            text = str(asset.meta["transcript"])
        if not task.min_words <= service.word_count(text) <= task.max_words:
            raise service.CurriculumError(f"write or speak between {task.min_words} and {task.max_words} words", 422)
        result = service.assess_productive(
            session, settings, providers, learner_id=learner_id, stage_id=bank.stage_id, task=task, text=text,
            skill=skill, request_id=request_id,
            context=f"Reading source: {topic.reading.text.nl}\nListening source: {topic.listening.text.nl}",
        )
        completed = True  # A substantive practice attempt may still need improvement.
        evidence = {"text": text, "audio_asset_id": str(asset_id) if asset_id else None, "result": result.copy()}
    version = hashlib.sha256(topic.model_dump_json().encode()).hexdigest()
    statement = insert(TopicPractice).values(
        id=uuid.uuid4(), learner_id=learner_id, stage_id=bank.stage_id, topic_id=topic.id, skill=skill,
        completed=completed, latest_passed=result["passed"], content_version=version, evidence=evidence, updated_at=utcnow(),
    ).on_conflict_do_update(index_elements=["learner_id", "stage_id", "topic_id", "skill"], set_={
        "completed": TopicPractice.completed | completed, "latest_passed": result["passed"],
        "content_version": version, "evidence": evidence, "updated_at": utcnow(),
    }).returning(TopicPractice.completed)
    sticky_completed = session.execute(statement).scalar_one()
    # Aggregate readiness remains skill-specific. Topic IDs retained for evidence, never sent as UI marks.
    aggregate = {**evidence, "topic_id": topic.id, "content_version": version}
    session.execute(insert(CurriculumPractice).values(
        id=uuid.uuid4(), learner_id=learner_id, stage_id=bank.stage_id, skill=skill,
        completed=completed, evidence=aggregate, updated_at=utcnow(),
    ).on_conflict_do_update(index_elements=["learner_id", "stage_id", "skill"], set_={
        "completed": CurriculumPractice.completed | completed, "evidence": aggregate, "updated_at": utcnow(),
    }))
    return {**result, "completed": sticky_completed, "skill": skill}
