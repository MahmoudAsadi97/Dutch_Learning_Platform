"""Evidence for the steps that are not a conversation: answers to questions, help-ladder use,
the writing draft and the submitted message. Correctness is decided here against the mission
document, never in the browser."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from dlp.db.base import utcnow
from dlp.domains.content.schemas import (
    CheckpointPayload,
    ListeningPayload,
    MissionDocument,
    ReadingPayload,
    Step,
    WritingPayload,
)
from dlp.domains.content.service import get_mission, mission_document
from dlp.domains.practice.models import EvidenceRecord, PracticeSession
from dlp.domains.practice.service import PracticeError, record_evidence
from dlp.domains.progress.models import SkillRecord

WORD = re.compile(r"[\w'’-]+", re.UNICODE)


def word_count(text: str) -> int:
    return len(WORD.findall(text))


def _document(session: Session, practice: PracticeSession) -> MissionDocument:
    mission = get_mission(session, practice.mission_id)
    assert mission is not None
    return mission_document(mission)


def _step(document: MissionDocument, practice: PracticeSession, step_key: str) -> Step:
    step = next((s for s in document.steps if s.key == step_key), None)
    if step is None:
        raise PracticeError("step not found", status_code=404)
    if step.variant != practice.variant:
        raise PracticeError(f"step {step_key} belongs to the {step.variant} variant", status_code=409)
    if practice.status != "active":
        raise PracticeError("this session is closed", status_code=409)
    return step


def _set_progress(practice: PracticeSession, step_key: str, **fields: Any) -> dict[str, Any]:
    progress = dict(practice.state.get("step_progress") or {})
    entry = {**progress.get(step_key, {}), **fields}
    progress[step_key] = entry
    practice.state = {**practice.state, "step_progress": progress}
    practice.current_step_key = step_key
    practice.updated_at = utcnow()
    return entry


def _skill_record(session: Session, practice: PracticeSession, skill: str) -> SkillRecord | None:
    from sqlalchemy import select

    return session.scalar(
        select(SkillRecord).where(SkillRecord.learner_id == practice.learner_id,
                                  SkillRecord.mission_id == practice.mission_id, SkillRecord.skill == skill)
    )


def _touch_skill(session: Session, practice: PracticeSession, step: Step, completed: bool, summary: dict[str, Any]) -> None:
    record = _skill_record(session, practice, step.skill)
    if record is None:
        return
    if record.status == "not_started":
        record.status = "in_progress"
        record.attempts = record.attempts + 1
    if completed and record.status in ("not_started", "in_progress"):
        record.status = "practised"
    assessment = dict(record.latest_assessment or {})
    assessment[step.key] = {"completed": completed, "session_id": str(practice.id), **summary}
    record.latest_assessment = assessment
    session.expire(practice, ["evidence"])
    record.evidence_ids = [str(e.id) for e in practice.evidence if e.skill == step.skill][-50:]


# --- answers ---------------------------------------------------------------------------------------------------------


@dataclass
class AnswerOutcome:
    evidence: EvidenceRecord
    correct: bool
    answer_index: int
    step_completed: bool
    answered: dict[str, bool]


def submit_answer(session: Session, practice: PracticeSession, *, step_key: str, question_id: str,
                  chosen_index: int) -> AnswerOutcome:
    document = _document(session, practice)
    step = _step(document, practice, step_key)
    payload = step.payload
    if not isinstance(payload, ReadingPayload | ListeningPayload):
        raise PracticeError("this step has no questions", status_code=400)
    question = next((q for q in payload.questions if q.id == question_id), None)
    if question is None:
        raise PracticeError("question not found", status_code=404)
    if not 0 <= chosen_index < len(question.options):
        raise PracticeError("chosen option out of range", status_code=422)
    correct = chosen_index == question.answer_index
    answered = dict((practice.state.get("step_progress") or {}).get(step_key, {}).get("answered", {}))
    attempt = int((practice.state.get("step_progress") or {}).get(step_key, {}).get("attempts", {}).get(question_id, 0)) + 1
    evidence = record_evidence(
        session, practice, step_key=step_key, skill=step.skill, kind="answer", modality="typed",
        payload={"question_id": question_id, "prompt_nl": question.prompt.nl, "chosen_index": chosen_index,
                 "chosen_nl": question.options[chosen_index].nl, "answer_index": question.answer_index,
                 "correct": correct, "attempt": attempt},
        source="learner",
    )
    answered[question_id] = correct or answered.get(question_id, False)
    attempts = dict((practice.state.get("step_progress") or {}).get(step_key, {}).get("attempts", {}))
    attempts[question_id] = attempt
    completed = all(q.id in answered for q in payload.questions)
    correct_count = sum(1 for q in payload.questions if answered.get(q.id))
    _set_progress(practice, step_key, answered=answered, attempts=attempts, completed=completed,
                  correct=correct_count, total=len(payload.questions))
    _touch_skill(session, practice, step, completed, {"correct": correct_count, "total": len(payload.questions)})
    return AnswerOutcome(evidence, correct, question.answer_index, completed, answered)


# --- help ladder -----------------------------------------------------------------------------------------------------


def record_help_use(session: Session, practice: PracticeSession, *, step_key: str, level: int, kind: str,
                    question_id: str = "") -> EvidenceRecord:
    document = _document(session, practice)
    step = _step(document, practice, step_key)
    if isinstance(step.payload, CheckpointPayload) and not step.payload.restrictions.help_ladder:
        raise PracticeError("help is not available in the checkpoint", status_code=403)
    if not 1 <= level <= document.help_policy.max_level:
        raise PracticeError(f"help level must be between 1 and {document.help_policy.max_level}", status_code=422)
    if kind in {"reading_translation", "listening_transcript"}:
        expected = ReadingPayload if kind == "reading_translation" else ListeningPayload
        if not isinstance(step.payload, expected) or question_id or level != 3:
            raise PracticeError("this support is not available for this step", status_code=422)
    else:
        rungs = getattr(step.payload, "help", [])
        if question_id:
            question = next((q for q in getattr(step.payload, "questions", []) if q.id == question_id), None)
            if question is None:
                raise PracticeError("question not found", status_code=404)
            rungs = question.help
        if not any(rung.level == level and rung.kind == kind for rung in rungs):
            raise PracticeError("help rung is not part of this lesson", status_code=422)
    # Record the first exposure once. Reopening or retrying after a lost response must not invent extra assistance.
    prior = session.scalars(select(EvidenceRecord).where(
        EvidenceRecord.session_id == practice.id, EvidenceRecord.step_key == step_key,
        EvidenceRecord.kind == "help_used",
    ))
    for item in prior:
        if (item.payload.get("level"), item.payload.get("kind"), item.payload.get("question_id") or "") == (
            level, kind, question_id,
        ):
            return item
    evidence = record_evidence(
        session, practice, step_key=step_key, skill=step.skill, kind="help_used", modality="none",
        payload={"level": level, "kind": kind, "question_id": question_id or None}, source="learner",
    )
    used = list((practice.state.get("step_progress") or {}).get(step_key, {}).get("help_levels", []))
    if level not in used:
        used.append(level)
    _set_progress(practice, step_key, help_levels=sorted(used))
    return evidence


# --- writing ---------------------------------------------------------------------------------------------------------


def save_draft(session: Session, practice: PracticeSession, *, step_key: str, text: str) -> dict[str, Any]:
    """Autosave: the draft lives in the session state, it is not evidence until submitted."""
    document = _document(session, practice)
    step = _step(document, practice, step_key)
    if not isinstance(step.payload, WritingPayload):
        raise PracticeError("this step has no draft", status_code=400)
    if len(text) > 4000:
        raise PracticeError("draft too long", status_code=413)
    drafts = dict(practice.state.get("drafts") or {})
    entry = {"text": text, "word_count": word_count(text), "saved_at": utcnow().isoformat()}
    drafts[step_key] = entry
    practice.state = {**practice.state, "drafts": drafts}
    practice.updated_at = utcnow()
    session.flush()
    return entry


@dataclass
class WritingOutcome:
    evidence: EvidenceRecord
    word_count: int
    missing: list[str]
    step_completed: bool


def submit_writing(session: Session, practice: PracticeSession, *, step_key: str, text: str) -> WritingOutcome:
    document = _document(session, practice)
    step = _step(document, practice, step_key)
    payload = step.payload
    if not isinstance(payload, WritingPayload):
        raise PracticeError("this step takes no written message", status_code=400)
    text = text.strip()
    count = word_count(text)
    if count < payload.min_words:
        raise PracticeError(f"the message has {count} words; at least {payload.min_words} are needed", status_code=422)
    if count > payload.max_words:
        raise PracticeError(f"the message has {count} words; at most {payload.max_words} are allowed", status_code=413)
    lowered = text.lower()
    missing = [item for item in payload.must_include if item.lower() not in lowered]
    submissions = int((practice.state.get("step_progress") or {}).get(step_key, {}).get("submissions", 0)) + 1
    evidence = record_evidence(
        session, practice, step_key=step_key, skill=step.skill, kind="typed_text", modality="typed",
        payload={"text": text, "word_count": count, "min_words": payload.min_words, "max_words": payload.max_words,
                 "must_include": list(payload.must_include), "missing": missing, "submission": submissions},
        source="learner",
    )
    drafts = dict(practice.state.get("drafts") or {})
    drafts[step_key] = {"text": text, "word_count": count, "saved_at": utcnow().isoformat(), "submitted": True}
    practice.state = {**practice.state, "drafts": drafts}
    _set_progress(practice, step_key, completed=True, submissions=submissions, word_count=count, missing=missing)
    _touch_skill(session, practice, step, True, {"word_count": count, "missing": missing})
    return WritingOutcome(evidence, count, missing, True)
