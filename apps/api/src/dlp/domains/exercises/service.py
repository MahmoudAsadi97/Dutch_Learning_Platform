"""Exercise sessions: create (seeded, idempotent, resumable), view, answer, skip, finish, export.

Items are generated once at creation from a seed (learner, request id, generator version) and stored with
their keys; reading a session never regenerates it. Every write locks the session row first and reads the
latest item state after the lock, so a double click, two tabs or a retry give one attempt, one award and one
mistake row. A repeated request id replays the stored response; the same id with another answer is refused.

The rules (roadmap 3.3, D-28): at most two attempts per item; a first miss or skip is asked once more at the
end with its options reshuffled, after the correct answer was shown; nothing blocks finishing. An item earns
its point with its first real answer, right or wrong (a skip is not an answer), so finishing early never pays
right answers more than wrong ones; a session with five answered items earns the session bonus. A
first-attempt miss writes a mistake row only for a word met before this session.
"""
from __future__ import annotations

import hashlib
import json
import random
import uuid
from datetime import timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from dlp.db.base import utcnow
from dlp.domains.activity.service import reached, record_activity, replayed
from dlp.domains.curriculum.schemas import STAGE_IDS
from dlp.domains.exercises import graders, mistakes
from dlp.domains.exercises.blueprints import SIZES, plan
from dlp.domains.exercises.generators import GENERATOR_VERSION
from dlp.domains.exercises.models import ExerciseItem, ExerciseSession, LearnerMistake, WordSuggestion
from dlp.domains.exercises.pool import pool_for
from dlp.domains.exercises.schemas import AnswerValue, CreateBody
from dlp.domains.exercises.taxonomy import category_for
from dlp.domains.identity.models import Learner
from dlp.domains.profile import service as profiles
from dlp.errors import DomainError

MAX_ATTEMPTS = 2
RESUME_HOURS = 12
SESSION_BONUS_MIN_ITEMS = 5
# skip reasons that close an item without counting it as missed; only kinds with audio accept them
AUDIO_SKIPS = ("no_microphone", "no_audio")
AUDIO_KINDS: frozenset[str] = frozenset()


class ExerciseError(DomainError):
    code = "exercise"

    def __init__(self, detail: str, status_code: int = 400, **kwargs) -> None:
        super().__init__(detail, status_code, **kwargs)


def fingerprint(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def seed_for(learner_id: uuid.UUID, request_id: str) -> int:
    """63 bits, so the seed fits PostgreSQL's signed BIGINT."""
    digest = hashlib.sha256(f"{learner_id}:{request_id}:{GENERATOR_VERSION}".encode()).digest()
    return int.from_bytes(digest[:8], "big") & (2**63 - 1)


# --- create ------------------------------------------------------------------------------------------------

def create(session: Session, learner: Learner, body: CreateBody) -> tuple[ExerciseSession, str]:
    """The session for this request id and how it was found: "replayed" (the same request again), "resumed" (an
    open one of the same kind) or "created"."""
    # Serialize starts for this learner, including when there is no session row to lock yet. FOR NO KEY UPDATE
    # does not block the key-share locks that foreign-key checks of a concurrent answer take on this row.
    session.execute(select(Learner.id).where(Learner.id == learner.id).with_for_update(key_share=True)).one()
    params = body.model_dump(exclude={"request_id"})
    signature = fingerprint(params)
    existing = session.scalar(select(ExerciseSession).where(ExerciseSession.learner_id == learner.id,
                                                            ExerciseSession.request_id == body.request_id))
    if existing is not None:
        if existing.params.get("fingerprint") != signature:
            raise ExerciseError("this request id already started a different session", 409)
        return existing, "replayed"
    stage_id = body.stage_id or profiles.ensure(session, learner).stage_id
    if stage_id not in STAGE_IDS:
        raise ExerciseError("learning stage not found", 404)
    pool = pool_for(stage_id)
    if not pool.variety.enabled:
        raise ExerciseError("there is not enough practice material at this stage yet", 409, code="not_ready")
    if body.library_topic is not None and body.library_topic not in pool.by_topic:
        raise ExerciseError("library topic not found", 404)
    now = utcnow()
    for row in session.scalars(select(ExerciseSession).where(
            ExerciseSession.learner_id == learner.id, ExerciseSession.status == "active",
            ExerciseSession.source == body.source, ExerciseSession.stage_id == stage_id,
            ExerciseSession.focus == body.focus).order_by(ExerciseSession.created_at.desc())):
        if row.params.get("library_topic") != body.library_topic:
            continue
        if not body.fresh and row.created_at >= now - timedelta(hours=RESUME_HOURS):
            return row, "resumed"
        row.status, row.updated_at = "abandoned", now
    seed = seed_for(learner.id, body.request_id)
    drafts = plan(pool, random.Random(seed), size=body.size or SIZES[body.source],
                  met=mistakes.met_words(session, learner.id), last_seen=mistakes.last_practised(session, learner.id),
                  library_topic=body.library_topic)
    if not any(draft.kind != "intro" for draft in drafts):
        raise ExerciseError("there is nothing to practise here yet", 409, code="not_ready")
    row = ExerciseSession(learner_id=learner.id, request_id=body.request_id, source=body.source, stage_id=stage_id,
                          focus=body.focus, seed=seed, generator_version=GENERATOR_VERSION,
                          content_version=pool.content_version, params={**params, "fingerprint": signature},
                          status="active", item_count=len(drafts), created_at=now, updated_at=now)
    session.add(row)
    session.flush()
    for position, draft in enumerate(drafts):
        session.add(ExerciseItem(session_id=row.id, learner_id=learner.id, position=position, kind=draft.kind,
                                 skill=draft.skill, ref=draft.ref, word=draft.word, prompt=draft.prompt,
                                 key=draft.key, attempts=[]))
    session.flush()
    return row, "created"


# --- reading -----------------------------------------------------------------------------------------------

def get(session: Session, learner_id: uuid.UUID, session_id: uuid.UUID, *, lock: bool = False) -> ExerciseSession:
    query = select(ExerciseSession).where(ExerciseSession.id == session_id, ExerciseSession.learner_id == learner_id)
    if lock:
        # items are read, modified and written as JSON; read the latest state after acquiring the lock
        query = query.with_for_update().execution_options(populate_existing=True)
    row = session.scalar(query)
    if row is None:
        raise ExerciseError("exercise session not found", 404)
    return row


def items(session: Session, row: ExerciseSession) -> list[ExerciseItem]:
    return list(session.scalars(select(ExerciseItem).where(ExerciseItem.session_id == row.id)
                                .order_by(ExerciseItem.position).execution_options(populate_existing=True)))


def _attempts_left(item: ExerciseItem) -> int:
    if item.closed:
        return 0
    return 1 if item.kind == "intro" else MAX_ATTEMPTS - len(item.attempts)


def _prompt(row: ExerciseSession, item: ExerciseItem) -> dict[str, Any]:
    """An item asked again has its options in a new order."""
    prompt = dict(item.prompt)
    if item.attempts and not item.closed and "options" in prompt:
        options = list(prompt["options"])
        random.Random(f"{row.seed}:{item.position}:{len(item.attempts) + 1}").shuffle(options)
        prompt["options"] = options
    return prompt


def _queue(rows: list[ExerciseItem]) -> list[ExerciseItem]:
    """Open items in order, then the ones missed once."""
    return sorted((item for item in rows if not item.closed), key=lambda item: (bool(item.attempts), item.position))


def progress(rows: list[ExerciseItem]) -> dict[str, int]:
    graded = [item for item in rows if item.kind != "intro"]
    return {"closed": sum(item.closed for item in graded), "total": len(graded),
            "queued": sum(1 for item in graded if item.attempts and not item.closed)}


def item_view(row: ExerciseSession, item: ExerciseItem) -> dict[str, Any]:
    return {"id": item.id, "position": item.position, "kind": item.kind, "skill": item.skill,
            "state": "closed" if item.closed else "open", "attempts_left": _attempts_left(item),
            "prompt": _prompt(row, item),
            "feedback": item.attempts[-1]["response"]["feedback"] if item.closed and item.attempts else None}


def session_view(row: ExerciseSession, rows: list[ExerciseItem], *, resumed: bool = False) -> dict[str, Any]:
    queue = _queue(rows) if row.status == "active" else []
    return {"id": row.id, "source": row.source, "stage_id": row.stage_id, "focus": row.focus,
            "library_topic": row.params.get("library_topic"), "status": row.status, "resumed": resumed,
            "items": [item_view(row, item) for item in rows], "next_item_id": queue[0].id if queue else None,
            "progress": progress(rows), "summary": row.summary or None}


# --- answering ---------------------------------------------------------------------------------------------

def _feedback(item: ExerciseItem, outcome: str, option: str | None) -> dict[str, Any]:
    if item.kind == "intro":
        return {"outcome": outcome}
    key = item.key
    return {"outcome": outcome, "correct": key["answer"], "given": option, "support": key.get("support", []),
            "explanation": key.get("explanation"), "word": key.get("word"), "sentence": key.get("sentence"),
            "odd_topic": key.get("odd_topic")}


def _record_mistake(session: Session, row: ExerciseSession, item: ExerciseItem, *, option: str | None,
                    outcome: str, request_id: str) -> None:
    key = item.key
    authored = bool(key.get("authored"))
    # odd one out: the word the learner took for the odd one is the word they did not place
    odd = item.kind == "odd_one_out"
    lemma = key.get("words", {}).get(option, "") if odd else item.word
    if not authored and (not lemma or lemma not in key.get("met", [])):
        return  # a first encounter, not a mistake
    support = {entry["id"]: entry for entry in key.get("support", [])}
    mistakes.record_mistake(
        session, learner_id=row.learner_id, source="exercise", source_id=str(item.id), stage_id=row.stage_id,
        category=category_for(item.kind, authored=authored), skill=item.skill, kind=item.kind,
        ref=key.get("refs", {}).get(option, "") if odd else item.ref,
        lemma=lemma, given=support.get(option, {}).get("nl", "") if option else "",
        expected=support.get(key["answer"], {}).get("nl", ""), request_id=request_id,
        detail={"outcome": outcome, "direction": item.prompt.get("direction"), "option": option},
    )


def respond(session: Session, learner_id: uuid.UUID, session_id: uuid.UUID, item_id: uuid.UUID, *, request_id: str,
            answer: AnswerValue | None = None, skip: str | None = None, hint_used: bool = False) -> dict[str, Any]:
    """Answer (`answer`) or skip (`skip`, with its reason) one item."""
    row = get(session, learner_id, session_id, lock=True)
    rows = items(session, row)
    item = next((candidate for candidate in rows if candidate.id == item_id), None)
    if item is None:
        raise ExerciseError("exercise item not found", 404)
    signature = fingerprint({"answer": answer.model_dump() if answer else None, "skip": skip})
    previous = next((attempt for attempt in item.attempts if attempt["request_id"] == request_id), None)
    if previous is not None:
        if previous["answer_hash"] != signature:
            raise ExerciseError("this request id belongs to a different answer", 409)
        return {**previous["response"], **replayed(session, learner_id, request_id)}
    if row.status != "active":
        raise ExerciseError("this exercise session is already finished", 409, code="session_closed")
    if item.closed:
        raise ExerciseError("this item is already answered", 409, code="already_answered")
    option = answer.option if answer else None
    if skip in AUDIO_SKIPS and item.kind not in AUDIO_KINDS:
        raise ExerciseError("this item has no audio to skip for", 422)
    if skip is not None:
        outcome = "done" if item.kind == "intro" else "skipped"
    elif item.kind == "intro":
        if not (answer and answer.done):
            raise ExerciseError("an intro card is closed with done", 422)
        outcome = "done"
    else:
        if option not in {entry["id"] for entry in item.prompt["options"]}:
            raise ExerciseError("choose one of the item's options", 422)
        outcome = graders.grade(item.kind, item.key, option)
    attempt = len(item.attempts) + 1
    closed = outcome in ("correct", "done") or attempt >= MAX_ATTEMPTS or skip in AUDIO_SKIPS
    if attempt == 1:
        item.first_outcome = outcome
        if outcome in ("incorrect", "skipped") and skip in (None, "unknown"):
            _record_mistake(session, row, item, option=option, outcome=outcome, request_id=request_id)
    award = None
    if item.kind != "intro" and outcome != "skipped" and not _answered(item):
        # the first real answer earns the item's point, right or wrong
        award = record_activity(session, learner_id, kind="exercise_item", ref=str(item.id), request_id=request_id,
                                meta={"kind": item.kind, "session": str(row.id)})
        item.points_awarded = award.points
    now = utcnow()
    item.closed = closed
    item.hint_used = item.hint_used or hint_used
    if closed:
        item.answered_at = now
    response: dict[str, Any] = {
        "item_id": str(item.id), "attempt": attempt, "outcome": outcome, "closed": closed,
        "requeue": not closed, "attempts_left": 0 if closed else MAX_ATTEMPTS - attempt,
        "feedback": _feedback(item, outcome, option), "points": award.points if award else 0,
    }
    item.attempts = [*item.attempts, {"request_id": request_id, "answer_hash": signature, "outcome": outcome,
                                      "at": now.isoformat(), "response": response}]
    queue = _queue(rows)
    response.update(progress=progress(rows), next_item_id=str(queue[0].id) if queue else None)
    item.attempts = [*item.attempts[:-1], {**item.attempts[-1], "response": response}]
    row.updated_at = now
    session.flush()
    return {**response, **reached(award)}


# --- finishing ---------------------------------------------------------------------------------------------

def _answered(item: ExerciseItem) -> bool:
    """The learner answered it at least once (a skip is not an answer)."""
    return any(attempt["outcome"] != "skipped" for attempt in item.attempts)


def _summary(rows: list[ExerciseItem], bonus: int) -> dict[str, Any]:
    graded = [item for item in rows if item.kind != "intro"]
    by_kind: dict[str, dict[str, int]] = {}
    for item in graded:
        counts = by_kind.setdefault(item.kind, {"total": 0, "first_try_correct": 0})
        counts["total"] += 1
        counts["first_try_correct"] += item.first_outcome == "correct"
    missed = [item for item in graded if item.first_outcome in ("incorrect", "skipped")]
    return {
        "items_total": len(graded),
        "answered": sum(1 for item in graded if _answered(item)),
        "first_try_correct": sum(1 for item in graded if item.first_outcome == "correct"),
        "fixed_on_retry": sum(1 for item in missed if item.attempts and item.attempts[-1]["outcome"] == "correct"),
        "skipped": sum(1 for item in graded if item.first_outcome == "skipped"),
        "points_earned": sum(item.points_awarded for item in graded) + bonus,
        "session_bonus": bonus,
        "by_kind": by_kind,
        "missed": [{"ref": item.ref, "term": item.key.get("word", {}).get("term"),
                    "expected": next((entry.get("nl") for entry in item.key.get("support", [])
                                      if entry["id"] == item.key.get("answer")), None)} for item in missed],
        "suggestions": [],
    }


def finish(session: Session, learner_id: uuid.UUID, session_id: uuid.UUID, *, request_id: str,
           early: bool = False) -> dict[str, Any]:
    """Close the session with its summary. Idempotent: a finished session returns what it said the first time."""
    row = get(session, learner_id, session_id, lock=True)
    if row.status == "finished":
        # the request that finished it hears what it heard the first time; another one earns nothing
        same = row.summary.get("request_id") == request_id
        return {"id": row.id, "status": "finished", "summary": row.summary,
                "points": row.summary.get("session_bonus", 0) if same else 0,
                **replayed(session, learner_id, request_id)}
    if row.status != "active":
        raise ExerciseError("this exercise session was left unfinished", 409, code="session_closed")
    rows = items(session, row)
    graded = [item for item in rows if item.kind != "intro"]
    if not early and any(not item.closed for item in graded):
        raise ExerciseError("answer or skip every item first, or finish early", 409)
    bonus = None
    answered = sum(1 for item in graded if _answered(item))
    if answered >= SESSION_BONUS_MIN_ITEMS:
        bonus = record_activity(session, learner_id, kind="exercise_session", ref=str(row.id), request_id=request_id,
                                meta={"items": answered})
    summary = {**_summary(rows, bonus.points if bonus else 0), "request_id": request_id}
    summary["suggestions"] = mistakes.suggest_words(session, learner_id, [
        (item.word, item.key["word"]) for item in graded
        if item.first_outcome in ("incorrect", "skipped") and item.kind in ("choice", "cloze_choice")
        and item.word and "word" in item.key
    ])
    now = utcnow()
    row.summary, row.status, row.finished_at, row.updated_at = summary, "finished", now, now
    session.flush()
    return {"id": row.id, "status": "finished", "summary": summary, "points": bonus.points if bonus else 0,
            **reached(bonus)}


# --- export ------------------------------------------------------------------------------------------------

def export(session: Session, learner_id: uuid.UUID) -> dict[str, Any]:
    """Everything stored about the learner's practice, without any item's key."""
    rows = list(session.scalars(select(ExerciseSession).where(ExerciseSession.learner_id == learner_id)
                                .order_by(ExerciseSession.created_at)))
    all_items = list(session.scalars(select(ExerciseItem).where(ExerciseItem.learner_id == learner_id)
                                     .order_by(ExerciseItem.session_id, ExerciseItem.position)))
    by_session: dict[uuid.UUID, list[ExerciseItem]] = {}
    for item in all_items:
        by_session.setdefault(item.session_id, []).append(item)
    return {
        "sessions": [{
            "id": str(row.id), "source": row.source, "stage_id": row.stage_id, "focus": row.focus,
            "params": {k: v for k, v in row.params.items() if k != "fingerprint"}, "status": row.status,
            "generator_version": row.generator_version, "content_version": row.content_version,
            "summary": row.summary, "created_at": row.created_at.isoformat(),
            "finished_at": row.finished_at.isoformat() if row.finished_at else None,
            # an item's ref names its answer: only once the answer has been shown
            "items": [{"id": str(item.id), "position": item.position, "kind": item.kind,
                       "ref": item.ref if item.closed or item.attempts else None,
                       "prompt": item.prompt, "first_outcome": item.first_outcome, "closed": item.closed,
                       "hint_used": item.hint_used, "points": item.points_awarded,
                       "attempts": [{"outcome": a["outcome"], "at": a["at"],
                                     "given": a["response"]["feedback"].get("given")} for a in item.attempts],
                       "answered_at": item.answered_at.isoformat() if item.answered_at else None}
                      for item in by_session.get(row.id, [])],
        } for row in rows],
        "mistakes": [{"id": str(m.id), "source": m.source, "source_id": m.source_id, "stage_id": m.stage_id,
                      "skill": m.skill, "kind": m.kind, "category": m.category,
                      "taxonomy_version": m.taxonomy_version, "ref": m.ref, "lemma": m.lemma, "given": m.given,
                      "expected": m.expected, "quote": m.quote, "assessed": m.assessed, "detail": m.detail,
                      "resolved_at": m.resolved_at.isoformat() if m.resolved_at else None,
                      "created_at": m.created_at.isoformat()}
                     for m in session.scalars(select(LearnerMistake).where(LearnerMistake.learner_id == learner_id)
                                              .order_by(LearnerMistake.created_at))],
        "word_suggestions": [{"key": s.key, "term": s.term, "meaning_en": s.meaning_en, "meaning_fa": s.meaning_fa,
                              "source_id": s.source_id, "reason": s.reason, "miss_count": s.miss_count,
                              "status": s.status, "created_at": s.created_at.isoformat(),
                              "updated_at": s.updated_at.isoformat()}
                             for s in session.scalars(select(WordSuggestion)
                                                      .where(WordSuggestion.learner_id == learner_id)
                                                      .order_by(WordSuggestion.created_at))],
    }
