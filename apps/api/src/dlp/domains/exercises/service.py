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

A practice topic or a stage lesson is a session too (activities.py): a passage step, then the authored
questions, whose first answers complete the activity at finish by the course's own rule; or, for a topic's
speaking or writing, a warm-up on its words that completes nothing.
"""
from __future__ import annotations

import hashlib
import json
import random
import uuid
from datetime import timedelta
from typing import Any, get_args

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from dlp.config import Settings
from dlp.db.base import utcnow
from dlp.domains.activity.service import reached, record_activity, replayed
from dlp.domains.curriculum.schemas import STAGE_IDS
from dlp.domains.exercises import activities, graders, mistakes
from dlp.domains.exercises.blueprints import SIZES, plan
from dlp.domains.exercises.compare import ARTICLES, fold
from dlp.domains.exercises.generators import GENERATOR_VERSION
from dlp.domains.exercises.models import ExerciseItem, ExerciseSession, LearnerMistake, WordSuggestion
from dlp.domains.exercises.pool import pool_for
from dlp.domains.exercises.schemas import AnswerValue, CreateBody, GradedKind
from dlp.domains.exercises.taxonomy import category_for
from dlp.domains.identity.models import Learner
from dlp.domains.profile import service as profiles
from dlp.domains.speech.compare import read_aloud_compare
from dlp.domains.speech.service import synthesize_cached, transcribe_upload
from dlp.domains.usage import service as usage
from dlp.errors import DomainError
from dlp.providers.base import BlobStore, SpeechToText, TextToSpeech

MAX_ATTEMPTS = 2
RESUME_HOURS = 12
SESSION_BONUS_MIN_ITEMS = 5
# skip reasons that close an item without counting it as missed; only kinds with audio accept them
AUDIO_SKIPS = ("no_microphone", "no_audio")
AUDIO_KINDS = frozenset({"listen_choose", "dictation", "shadow"})
# steps with nothing to answer: closed with done (or any skip), never graded, never a point or a mistake
UNGRADED = frozenset({"intro"}) | activities.PASSAGE_KINDS
# a first outcome that counts as right the first time: shadowing is heard, never "correct"
FIRST_TRY_RIGHT = ("correct", "heard")
# a session plans speech only while this many audio seconds of the allowance are left (a cached sound is free,
# a new one or a recording costs seconds)
AUDIO_MIN_SECONDS = 60.0


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

def _audio_left(session: Session, settings: Settings, learner_id: uuid.UUID) -> float:
    counters = usage.snapshot(session, settings, learner_id)["counters"]["audio_seconds"]
    return min(counters["daily"]["remaining"], counters["total"]["remaining"])


# CreateBody fields added after the first sessions: left out of the fingerprint at their defaults, so a request
# id sent before they existed keeps its fingerprint
_ADDED_FIELDS = {"topic_id": None, "skill": None, "retry": False}


def _params(body: CreateBody) -> dict[str, Any]:
    defaults = {name for name, default in _ADDED_FIELDS.items() if getattr(body, name) == default}
    return body.model_dump(exclude={"request_id", *defaults})


def _last_finished(session: Session, learner_id: uuid.UUID, body: CreateBody,
                   stage_id: str) -> ExerciseSession | None:
    """The learner's last finished session on this activity (a retry or not)."""
    return session.scalar(select(ExerciseSession).where(
        ExerciseSession.learner_id == learner_id, ExerciseSession.status == "finished",
        ExerciseSession.source == body.source, ExerciseSession.stage_id == stage_id,
        ExerciseSession.topic_id == (body.topic_id or ""), ExerciseSession.skill == body.skill,
    ).order_by(ExerciseSession.finished_at.desc()).limit(1))


def _to_retry(session: Session, last: ExerciseSession | None) -> set[str]:
    """The questions the last finished session on this activity did not get right the first time (wrong,
    skipped or never tried); a retry session asks only those."""
    missed = {item.key["question"] for item in (items(session, last) if last else [])
              if item.key.get("authored") and item.first_outcome not in FIRST_TRY_RIGHT}
    if not missed:
        raise ExerciseError("there is no missed question to practise again", 409, code="nothing_to_retry")
    return missed


def create(session: Session, settings: Settings, learner: Learner, body: CreateBody) -> tuple[ExerciseSession, str]:
    """The session for this request id and how it was found: "replayed" (the same request again), "resumed" (an
    open one of the same kind) or "created"."""
    # Serialize starts for this learner, including when there is no session row to lock yet. FOR NO KEY UPDATE
    # does not block the key-share locks that foreign-key checks of a concurrent answer take on this row.
    session.execute(select(Learner.id).where(Learner.id == learner.id).with_for_update(key_share=True)).one()
    params = _params(body)
    signature = fingerprint(params)
    existing = session.scalar(select(ExerciseSession).where(ExerciseSession.learner_id == learner.id,
                                                            ExerciseSession.request_id == body.request_id))
    if existing is not None:
        if existing.params.get("fingerprint") != signature:
            raise ExerciseError("this request id already started a different session", 409)
        return existing, "replayed"
    if body.topic_id is not None:
        stage_id = body.stage_id or activities.stage_of(body.topic_id)
        if activities.stage_of(body.topic_id) != stage_id:
            raise ExerciseError("practice topic not found", 404)
    else:
        stage_id = body.stage_id or profiles.ensure(session, learner).stage_id
    if stage_id not in STAGE_IDS:
        raise ExerciseError("learning stage not found", 404)
    activity = activities.activity_for(stage_id, topic_id=body.topic_id, skill=body.skill) if body.skill else None
    receptive = activity is not None and activity.skill in activities.RECEPTIVE
    pool = None
    if not receptive:  # authored comprehension needs no word pool: the library's gate is not its gate
        pool = pool_for(stage_id)
        if not pool.variety.enabled:
            raise ExerciseError("there is not enough practice material at this stage yet", 409, code="not_ready")
        if body.library_topic is not None and body.library_topic not in pool.by_topic:
            raise ExerciseError("library topic not found", 404)
    now = utcnow()
    # a retry is built from the misses of the last finished session on the activity
    last = _last_finished(session, learner.id, body, stage_id) if body.retry else None
    for row in session.scalars(select(ExerciseSession).where(
            ExerciseSession.learner_id == learner.id, ExerciseSession.status == "active",
            ExerciseSession.source == body.source, ExerciseSession.stage_id == stage_id,
            ExerciseSession.focus == body.focus, ExerciseSession.topic_id == (body.topic_id or ""),
            ExerciseSession.skill == (body.skill or "")).order_by(ExerciseSession.created_at.desc())):
        if (row.params.get("library_topic") != body.library_topic or row.params.get("kinds") != body.kinds
                or row.params.get("retry", False) != body.retry):
            continue  # another library topic, kinds this client may not show, or a retry and a full session
        if ((activity is not None and row.content_version != activity.content_version)
                or (body.retry and row.params.get("retry_of") != (str(last.id) if last else None))):
            # built on content changed since (it could never count), or a retry of an older session's misses
            row.status, row.updated_at = "abandoned", now
            continue
        if not body.fresh and row.created_at >= now - timedelta(hours=RESUME_HOURS):
            return row, "resumed"
        row.status, row.updated_at = "abandoned", now
    seed = seed_for(learner.id, body.request_id)
    rng = random.Random(seed)
    if activity is not None and receptive:
        drafts = activities.comprehension(activity, rng, only=_to_retry(session, last) if body.retry else None)
        content_version = activity.content_version
    else:
        assert pool is not None
        kinds = frozenset(body.kinds) if body.kinds else None
        if activity is not None and activity.topic is not None:
            # a warm-up on the topic's own words; a Story Time paragraph to order would be about something else
            content_version = activity.content_version
            drafts = plan(pool, rng, size=activities.WARM_UP_SIZE, met=mistakes.met_words(session, learner.id),
                          last_seen=mistakes.last_practised(session, learner.id),
                          audio=_audio_left(session, settings, learner.id) >= AUDIO_MIN_SECONDS,
                          kinds=(kinds or frozenset(get_args(GradedKind))) - {"sentence_order"},
                          only=frozenset(activity.topic.vocabulary_ids))
        else:
            content_version = pool.content_version
            drafts = plan(pool, rng, size=body.size or SIZES[body.source],
                          met=mistakes.met_words(session, learner.id),
                          last_seen=mistakes.last_practised(session, learner.id),
                          library_topic=body.library_topic, typing=body.source != "while_you_wait",
                          audio=_audio_left(session, settings, learner.id) >= AUDIO_MIN_SECONDS, kinds=kinds)
    if not any(draft.kind not in UNGRADED for draft in drafts):
        raise ExerciseError("there is nothing to practise here yet", 409, code="not_ready")
    row = ExerciseSession(learner_id=learner.id, request_id=body.request_id, source=body.source, stage_id=stage_id,
                          topic_id=body.topic_id or "", skill=body.skill or "", focus=body.focus, seed=seed,
                          generator_version=GENERATOR_VERSION, content_version=content_version,
                          params={**params, "fingerprint": signature,
                                  **({"retry_of": str(last.id)} if body.retry and last else {})},
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
    return 1 if item.kind in UNGRADED else MAX_ATTEMPTS - len(item.attempts)


def _solved(item: ExerciseItem, name: str, pieces: list[dict[str, Any]]) -> bool:
    """The pieces as shown already read as the answer: the right column lined up with the left, or tiles and
    sentences whose text is the solution (two identical tiles swapped still read solved)."""
    key = item.key
    if name == "right":
        return [piece["id"] for piece in pieces] == [key["pairs"][left["id"]] for left in item.prompt["left"]]
    if name in ("tiles", "sentences"):
        return [fold(piece["nl"]) for piece in pieces] == [fold(text) for text in key["texts"]]
    return False


def _prompt(row: ExerciseSession, item: ExerciseItem, *, reveal: bool = False) -> dict[str, Any]:
    """An item asked again has its options, pieces or sentences in a new order, never one that reads solved. A
    passage shows its translation, or its transcript, once `reveal` says its questions are answered."""
    prompt = dict(item.prompt)
    if item.kind in activities.PASSAGE_KINDS:
        if reveal:
            prompt["text" if item.kind == "read_passage" else "transcript"] = item.key["reveal"]
        return prompt
    if not item.attempts or item.closed:
        return prompt
    rng = random.Random(f"{row.seed}:{item.position}:{len(item.attempts) + 1}")
    for name in ("options", "right", "tiles", "sentences"):
        if name in prompt:
            pieces = list(prompt[name])
            for _ in range(50):
                rng.shuffle(pieces)
                if not _solved(item, name, pieces):
                    break
            prompt[name] = pieces
    return prompt


def _retried_later(item: ExerciseItem) -> bool:
    """Missed once and asked again at the end; a shadowing take not heard is tried again at once."""
    return bool(item.attempts) and not item.closed and item.kind != "shadow"


def _queue(rows: list[ExerciseItem]) -> list[ExerciseItem]:
    """Open items in order, then the ones missed once."""
    return sorted((item for item in rows if not item.closed), key=lambda item: (_retried_later(item), item.position))


def progress(rows: list[ExerciseItem]) -> dict[str, int]:
    graded = [item for item in rows if item.kind not in UNGRADED]
    return {"closed": sum(item.closed for item in graded), "total": len(graded),
            "queued": sum(1 for item in graded if _retried_later(item))}


def item_view(row: ExerciseSession, item: ExerciseItem, *, reveal: bool = False) -> dict[str, Any]:
    return {"id": item.id, "position": item.position, "kind": item.kind, "skill": item.skill,
            "state": "closed" if item.closed else "open", "attempts_left": _attempts_left(item),
            "prompt": _prompt(row, item, reveal=reveal), "hint_used": bool(item.hint_used),
            "feedback": item.attempts[-1]["response"]["feedback"] if item.closed and item.attempts else None}


def _revealed(row: ExerciseSession, rows: list[ExerciseItem]) -> bool:
    """A passage's translation or transcript is shown once every question about it is closed, or the session
    has ended."""
    return row.status != "active" or all(item.closed for item in rows if item.key.get("authored"))


def session_view(row: ExerciseSession, rows: list[ExerciseItem], *, resumed: bool = False) -> dict[str, Any]:
    queue = _queue(rows) if row.status == "active" else []
    reveal = _revealed(row, rows)
    return {"id": row.id, "source": row.source, "stage_id": row.stage_id, "focus": row.focus,
            "library_topic": row.params.get("library_topic"), "topic_id": row.topic_id or None,
            "skill": row.skill or None, "retry": bool(row.params.get("retry")), "status": row.status,
            "resumed": resumed, "items": [item_view(row, item, reveal=reveal) for item in rows],
            "next_item_id": queue[0].id if queue else None, "progress": progress(rows),
            "summary": row.summary or None}


# --- answering ---------------------------------------------------------------------------------------------

def _feedback(item: ExerciseItem, outcome: str, judged: graders.Judgement | None) -> dict[str, Any]:
    """What the answer may now reveal: the key's answer, glosses, word cards and the grader's verdict."""
    if item.kind in UNGRADED:
        return {"outcome": outcome}
    key = item.key
    feedback: dict[str, Any] = {
        "outcome": outcome, "correct": key.get("answer"), "support": key.get("support", []),
        "explanation": key.get("explanation"), "word": key.get("word"), "sentence": key.get("sentence"),
        "odd_topic": key.get("odd_topic"), "cards": key.get("cards"), "texts": key.get("texts"),
        "order": key.get("order"), "translation": key.get("translation"),
        "overridable": item.kind in graders.OVERRIDABLE and outcome in ("incorrect", "almost"),
    }
    if item.kind in graders.TYPED_KINDS:
        feedback["expected"] = key["accepted"][0]
    return {**feedback, **(judged.feedback if judged else {})}


def _word_missed(item: ExerciseItem, feedback: dict[str, Any] | None) -> bool:
    """Whether a miss is about the item's word. A dictated sentence can be wrong elsewhere (a word left out, a
    name heard otherwise) with the word itself typed right; then neither a mistake nor a word-bank suggestion
    lands on the word. A skipped dictation is a miss of the word, as for every other kind."""
    if item.kind != "dictation" or not feedback or "diff" not in feedback:
        return True
    own = set(fold(item.key["word"]["term"]).split()) - ARTICLES
    if len(fold(item.key["accepted"][0]).split()) <= len(own) + 1:
        return True  # the word alone (pre-A1)
    return any(op["op"] != "same" and own & set(fold(op["expected"]).split()) for op in feedback["diff"])


def _record_mistakes(session: Session, row: ExerciseSession, item: ExerciseItem, *, judged: graders.Judgement | None,
                     outcome: str, request_id: str) -> None:
    """A row per missed part on a word met before this session: the item's word, the word the learner took for
    the odd one, every wrong pair or noun of a board. A first encounter is not a mistake."""
    key = item.key
    if item.kind in graders.NO_MISTAKES or not _word_missed(item, judged.feedback if judged else None):
        return
    authored = bool(key.get("authored"))
    parts = judged.misses if judged else ["answer"]
    met = set(key.get("met", []))
    support = {entry["id"]: entry for entry in key.get("support", [])}
    for part in parts:
        if item.kind == "odd_one_out" or item.kind in ("match_pairs", "de_het"):
            lemma, ref = key.get("words", {}).get(part, ""), key.get("refs", {}).get(part, "")
        else:
            lemma, ref = item.word, item.ref
        if not authored and (not lemma or lemma not in met):
            continue
        given, expected = "", ""
        if item.kind in graders.OPTION_KINDS:
            given = support.get(part, {}).get("nl", "") if outcome != "skipped" else ""
            expected = support.get(key["answer"], {}).get("nl", "")
        elif item.kind in graders.TYPED_KINDS:
            given, expected = (judged.feedback.get("typed", "") if judged else ""), key["accepted"][0]
        elif item.kind == "match_pairs":
            # the meaning the learner matched with this word, and its own
            chosen = judged.feedback["pairs"][part]["given"] if judged else ""
            owner = next((left for left, right in key["pairs"].items() if right == chosen), None)
            given = key["cards"][owner]["meaning"]["en"] if owner else ""
            expected = key["cards"][part]["meaning"]["en"]
        elif item.kind == "de_het":
            card = key["cards"][part]
            given = f"{judged.feedback['bins'][part]['given']} {card['term'].split(' ', 1)[-1]}" if judged else ""
            expected = card["term"]
        elif item.kind == "sentence_builder":
            given = " ".join(key["texts"][key["order"].index(i)] for i in judged.feedback["given_order"]) if judged else ""
            expected = key["sentence"]
        many = item.kind in ("match_pairs", "de_het")
        mistakes.record_mistake(
            session, learner_id=row.learner_id, source="exercise",
            source_id=f"{item.id}:{part}" if many else str(item.id), stage_id=row.stage_id,
            category=category_for(item.kind, authored=authored), skill=item.skill, kind=item.kind, ref=ref,
            lemma=lemma, given=given, expected=expected, request_id=request_id,
            detail={"outcome": outcome, "direction": item.prompt.get("direction"), "part": part},
        )


def _lexicon(row: ExerciseSession) -> frozenset[str]:
    try:
        return pool_for(row.stage_id).lexicon
    except Exception:  # the real-word guard is a refinement; an unreadable library must not stop grading
        return frozenset()


def respond(session: Session, learner_id: uuid.UUID, session_id: uuid.UUID, item_id: uuid.UUID, *, request_id: str,
            answer: AnswerValue | None = None, skip: str | None = None, hint_used: bool = False) -> dict[str, Any]:
    """Answer (`answer`) or skip (`skip`, with its reason) one item."""
    row = get(session, learner_id, session_id, lock=True)
    rows = items(session, row)
    item = next((candidate for candidate in rows if candidate.id == item_id), None)
    if item is None:
        raise ExerciseError("exercise item not found", 404)
    given = answer.model_dump(exclude_none=True) if answer else {}
    signature = fingerprint({"answer": given or None, "skip": skip})
    previous = next((attempt for attempt in item.attempts if attempt["request_id"] == request_id), None)
    if previous is not None:
        if previous["answer_hash"] != signature:
            raise ExerciseError("this request id belongs to a different answer", 409)
        return {**previous["response"], **replayed(session, learner_id, request_id)}
    if row.status != "active":
        raise ExerciseError("this exercise session is already finished", 409, code="session_closed")
    if item.closed:
        raise ExerciseError("this item is already answered", 409, code="already_answered")
    _inherit_reading_assistance(rows)
    if skip in AUDIO_SKIPS and item.kind not in AUDIO_KINDS | {"listen_passage"}:
        raise ExerciseError("this item has no audio to skip for", 422)
    if item.kind == "shadow" and skip is None:
        raise ExerciseError("a shadowing item is answered with a recording", 422)
    judged: graders.Judgement | None = None
    if skip is not None:
        outcome = "done" if item.kind in UNGRADED else "skipped"
    elif item.kind in UNGRADED:
        if not given.get("done"):
            raise ExerciseError("this step is closed with done", 422)
        outcome = "done"
    else:
        try:
            judged = graders.grade(item.kind, item.prompt, item.key, given, _lexicon(row))
        except graders.InvalidAnswer as invalid:
            raise ExerciseError(str(invalid), 422) from invalid
        outcome = judged.outcome
    attempt = len(item.attempts) + 1
    # a shadowing item is not asked again at the end: skipped, it is done with
    closed = (outcome in ("correct", "almost", "done") or attempt >= MAX_ATTEMPTS or skip in AUDIO_SKIPS
              or item.kind == "shadow")
    if attempt == 1:
        item.first_outcome = outcome
        if outcome in ("incorrect", "skipped") and skip in (None, "unknown"):
            _record_mistakes(session, row, item, judged=judged, outcome=outcome, request_id=request_id)
    award = None
    if item.kind not in UNGRADED and outcome != "skipped" and not _answered(item):
        # the first real answer earns the item's point, right or wrong
        award = record_activity(session, learner_id, kind="exercise_item", ref=str(item.id), request_id=request_id,
                                meta={"kind": item.kind, "session": str(row.id)})
        item.points_awarded = award.points
    now = utcnow()
    item.closed = closed
    item.hint_used = item.hint_used or hint_used
    _inherit_reading_assistance(rows)
    if closed:
        item.answered_at = now
    response: dict[str, Any] = {
        "item_id": str(item.id), "attempt": attempt, "outcome": outcome, "closed": closed,
        "requeue": not closed, "attempts_left": 0 if closed else MAX_ATTEMPTS - attempt,
        "feedback": _feedback(item, outcome, judged), "points": award.points if award else 0,
    }
    # the learner's own answer is kept with the attempt (and exported); the response replays a retry
    item.attempts = [*item.attempts, {"request_id": request_id, "answer_hash": signature, "outcome": outcome,
                                      "at": now.isoformat(), "answer": given, "skip": skip, "response": response}]
    queue = _queue(rows)
    response.update(progress=progress(rows), next_item_id=str(queue[0].id) if queue else None)
    item.attempts = [*item.attempts[:-1], {**item.attempts[-1], "response": response}]
    row.updated_at = now
    session.flush()
    return {**response, **reached(award)}


def _item(session: Session, learner_id: uuid.UUID, session_id: uuid.UUID, item_id: uuid.UUID, *,
          lock: bool = False) -> tuple[ExerciseSession, list[ExerciseItem], ExerciseItem]:
    row = get(session, learner_id, session_id, lock=lock)
    rows = items(session, row)
    item = next((candidate for candidate in rows if candidate.id == item_id), None)
    if item is None:
        raise ExerciseError("exercise item not found", 404)
    return row, rows, item


def _inherit_reading_assistance(rows: list[ExerciseItem]) -> bool:
    """Reading a passage aloud supports every question about it, including after a reload.

    Primary listening audio is the task itself, so it does not set this flag.
    Only questions without a first answer inherit support. Listening to feedback
    after answering does not rewrite the earlier independent evidence.
    """
    assisted = any(item.kind == "read_passage" and item.hint_used for item in rows)
    if assisted:
        for item in rows:
            if item.key.get("authored") and item.first_outcome is None and not item.attempts:
                item.hint_used = True
    return assisted


def mark_assistance(session: Session, learner_id: uuid.UUID, session_id: uuid.UUID,
                    item_id: uuid.UUID) -> dict[str, Any]:
    """Persist support before it is delivered; repeated calls only keep the flag true.

    No answer, attempt, point, paid call or session completion is created here.
    The session lock serializes this with answering and finishing in another tab.
    """
    row, rows, item = _item(session, learner_id, session_id, item_id, lock=True)
    if row.status != "active":
        raise ExerciseError("this exercise session is already finished", 409, code="session_closed")
    if item.kind == "listen_passage":
        raise ExerciseError("primary listening audio is not reading assistance", 422)
    if item.closed and item.kind != "read_passage":
        raise ExerciseError("this item is already answered", 409, code="already_answered")
    item.hint_used = True
    _inherit_reading_assistance(rows)
    row.updated_at = utcnow()
    session.flush()
    return item_view(row, item, reveal=_revealed(row, rows))


def item_audio(session: Session, settings: Settings, *, learner_id: uuid.UUID, session_id: uuid.UUID,
               item_id: uuid.UUID, request_id: str, tts: TextToSpeech, blob: BlobStore) -> tuple[bytes, bool]:
    """The sound of an item with speech, from the speech cache (free when cached). No row is locked: hearing a
    sound again changes nothing in the session."""
    _row, _rows, item = _item(session, learner_id, session_id, item_id)
    if item.kind not in AUDIO_KINDS:
        raise ExerciseError("this item has no sound", 422)
    return synthesize_cached(session, settings, learner_id=learner_id, request_id=request_id,
                             text=item.key["audio_text"], tts=tts, blob=blob)


def record(session: Session, settings: Settings, *, learner_id: uuid.UUID, session_id: uuid.UUID,
           item_id: uuid.UUID, request_id: str, upload_bytes: bytes, upload_filename: str, stt: SpeechToText,
           blob: BlobStore) -> dict[str, Any]:
    """A shadowing attempt: the recording is transcribed (not kept) before the session row is locked, then the
    words heard are compared with the sentence. The outcome is heard or not heard, never a score (D-20, D-23);
    heard speech earns the item's point, and nothing is a mistake. A take not heard may be
    tried once more at once (a noisy room, a microphone that started late); heard, or a second take, closes it.

    One recording of an item is handled at a time (a transaction-scoped advisory lock on the item, taken before
    anything is read), so a retry or a second tap waits for the first, then replays it or finds the item
    answered, without paying for a second transcription. A refusal after a transcription is returned with its
    usage kept (`persist`), never rolled back."""
    session.execute(select(func.pg_advisory_xact_lock(func.hashtextextended(f"exercise-recording:{item_id}", 0))))
    row, _rows, item = _item(session, learner_id, session_id, item_id)
    if item.kind != "shadow":
        raise ExerciseError("only a shadowing item takes a recording", 422)
    previous = next((attempt for attempt in item.attempts if attempt["request_id"] == request_id), None)
    if previous is not None:
        return {**previous["response"], **replayed(session, learner_id, request_id)}
    if row.status != "active":
        raise ExerciseError("this exercise session is already finished", 409, code="session_closed")
    if item.closed:
        raise ExerciseError("this item is already answered", 409, code="already_answered")
    heard_text = transcribe_upload(session, settings, learner_id=learner_id, request_id=request_id,
                                   upload_bytes=upload_bytes, upload_filename=upload_filename, stt=stt, blob=blob,
                                   keep_recording=False).transcript.text
    row, rows, item = _item(session, learner_id, session_id, item_id, lock=True)
    previous = next((attempt for attempt in item.attempts if attempt["request_id"] == request_id), None)
    if previous is not None:
        return {**previous["response"], **replayed(session, learner_id, request_id)}
    if row.status != "active":  # finished or left while the recording was transcribed
        raise ExerciseError("this exercise session is already finished", 409, code="session_closed", persist=True)
    if item.closed:  # skipped while the recording was transcribed
        raise ExerciseError("this item is already answered", 409, code="already_answered", persist=True)
    words = read_aloud_compare(item.key["audio_text"], heard_text)
    outcome = "heard" if words["matched_words"] else "not_heard"  # any recognised word (D-23), no threshold
    item.first_outcome = item.first_outcome or outcome
    attempt = len(item.attempts) + 1
    closed = outcome == "heard" or attempt >= MAX_ATTEMPTS
    award = None
    if outcome == "heard":
        award = record_activity(session, learner_id, kind="exercise_item", ref=str(item.id), request_id=request_id,
                                meta={"kind": item.kind, "session": str(row.id)})
        item.points_awarded = award.points
    now = utcnow()
    item.closed = closed
    if closed:
        item.answered_at = now
    feedback = {"outcome": outcome, "word": item.key.get("word"), "sentence": item.key["audio_text"],
                "transcript": heard_text, **words}
    queue = _queue(rows)
    response: dict[str, Any] = {
        "item_id": str(item.id), "attempt": attempt, "outcome": outcome, "closed": closed,
        "requeue": False, "attempts_left": 0 if closed else MAX_ATTEMPTS - attempt, "feedback": feedback,
        "points": award.points if award else 0,
        "progress": progress(rows), "next_item_id": str(queue[0].id) if queue else None,
    }
    item.attempts = [*item.attempts, {"request_id": request_id, "answer_hash": "", "outcome": outcome,
                                      "at": now.isoformat(), "answer": {"transcript": heard_text}, "skip": None,
                                      "response": response}]
    row.updated_at = now
    session.flush()
    return {**response, **reached(award)}


def override(session: Session, learner_id: uuid.UUID, session_id: uuid.UUID, item_id: uuid.UUID, *,
             request_id: str) -> dict[str, Any]:
    """"Mijn antwoord klopt ook": the learner overrules the check of a typed answer or a built sentence. The item
    closes as accepted, its mistake row goes, its point stays what it was; nothing completes because of it."""
    row = get(session, learner_id, session_id, lock=True)
    rows = items(session, row)
    item = next((candidate for candidate in rows if candidate.id == item_id), None)
    if item is None:
        raise ExerciseError("exercise item not found", 404)
    if item.kind not in graders.OVERRIDABLE:
        raise ExerciseError("only a typed answer or a built sentence can be overruled", 422)
    if item.key.get("override"):
        return {**item.key["override"]["response"], **replayed(session, learner_id, request_id)}
    if row.status != "active":
        raise ExerciseError("this exercise session is already finished", 409, code="session_closed")
    last = item.attempts[-1] if item.attempts else None
    if last is None or last["outcome"] not in ("incorrect", "almost"):
        raise ExerciseError("there is no answer to overrule", 409)
    now = utcnow()
    session.execute(delete(LearnerMistake).where(LearnerMistake.learner_id == learner_id,
                                                 LearnerMistake.source == "exercise",
                                                 LearnerMistake.source_id == str(item.id)))
    item.closed = True
    item.answered_at = item.answered_at or now
    queue = _queue(rows)
    feedback = {**last["response"]["feedback"], "outcome": "accepted", "overridable": False}
    response = {"item_id": str(item.id), "attempt": len(item.attempts), "outcome": "accepted", "closed": True,
                "requeue": False, "attempts_left": 0, "feedback": feedback, "points": 0,
                "progress": progress(rows), "next_item_id": str(queue[0].id) if queue else None}
    item.key = {**item.key, "override": {"request_id": request_id, "at": now.isoformat(), "response": response}}
    item.attempts = [*item.attempts[:-1], {**last, "response": {**last["response"], "feedback": feedback}}]
    row.updated_at = now
    session.flush()
    return response


def reports(session: Session, *, limit: int = 200) -> list[dict[str, Any]]:
    """The learners' reports for the content review, newest first, without who sent them: the item's kind,
    ref, stage, prompt and right answer, and the reason and note (`python -m dlp.cli exercise-reports`)."""
    rows = session.execute(select(ExerciseItem, ExerciseSession.stage_id)
                           .join(ExerciseSession, ExerciseSession.id == ExerciseItem.session_id)
                           .where(ExerciseItem.key.has_key("report")))
    found = [{"item_id": str(item.id), "kind": item.kind, "ref": item.ref, "stage_id": stage_id,
              "reason": item.key["report"]["reason"], "note": item.key["report"]["note"],
              "at": item.key["report"]["at"], "prompt": item.prompt, "expected": _expected(item)}
             for item, stage_id in rows]
    return sorted(found, key=lambda entry: entry["at"], reverse=True)[:limit]


def report(session: Session, learner_id: uuid.UUID, session_id: uuid.UUID, item_id: uuid.UUID, *,
           request_id: str, reason: str, note: str | None) -> dict[str, Any]:
    """"Meld een probleem": the learner flags an item (a wrong answer key, an unclear prompt, a bad sound). Kept
    with the item for the content review, whatever its state; a later report replaces the earlier one. It
    changes nothing in the session."""
    row = get(session, learner_id, session_id, lock=True)
    item = next((candidate for candidate in items(session, row) if candidate.id == item_id), None)
    if item is None:
        raise ExerciseError("exercise item not found", 404)
    current = item.key.get("report") or {}
    signature = fingerprint({"reason": reason, "note": (note or "").strip()})
    if current.get("request_id") == request_id:
        if current.get("fingerprint", signature) != signature:
            raise ExerciseError("this request id belongs to a different report", 409)
    else:
        item.key = {**item.key, "report": {"request_id": request_id, "fingerprint": signature, "reason": reason,
                                           "note": (note or "").strip(), "at": utcnow().isoformat()}}
        session.flush()
    return {"item_id": item.id, "reason": item.key["report"]["reason"]}


# --- finishing ---------------------------------------------------------------------------------------------

def _answered(item: ExerciseItem) -> bool:
    """The learner answered it at least once (a skip is not an answer)."""
    return any(attempt["outcome"] != "skipped" for attempt in item.attempts)


def _first_miss(item: ExerciseItem) -> bool:
    """Missed or skipped on the first try; a skip because the sound or the microphone did not work is neither,
    and an answer the learner overruled is theirs to judge."""
    first = item.attempts[0] if item.attempts else {}
    return (item.first_outcome in ("incorrect", "skipped") and first.get("skip") not in AUDIO_SKIPS
            and not item.key.get("override"))


def _missed(item: ExerciseItem) -> list[dict[str, Any]]:
    """What the summary lists for a first-attempt miss: the word and its answer; a board, each word it missed."""
    key = item.key
    if item.kind in ("match_pairs", "de_het") and item.attempts:
        results = item.attempts[0]["response"]["feedback"].get("pairs" if item.kind == "match_pairs" else "bins") or {}
        return [{"ref": key["refs"][part], "term": key["cards"][part]["term"],
                 "expected": key["cards"][part]["meaning"]["en"] if item.kind == "match_pairs"
                 else key["cards"][part]["term"]} for part, result in results.items() if not result["ok"]]
    return [{"ref": item.ref, "term": key.get("word", {}).get("term"), "expected": _expected(item)}]


def _expected(item: ExerciseItem) -> str | None:
    key = item.key
    if item.kind in graders.TYPED_KINDS:
        return key["accepted"][0]
    if "sentence" in key and item.kind == "sentence_builder":
        return key["sentence"]
    return next((entry.get("nl") for entry in key.get("support", []) if entry["id"] == key.get("answer")), None)


def _summary(rows: list[ExerciseItem], bonus: int) -> dict[str, Any]:
    graded = [item for item in rows if item.kind not in UNGRADED]
    by_kind: dict[str, dict[str, int]] = {}
    for item in graded:
        counts = by_kind.setdefault(item.kind, {"total": 0, "first_try_correct": 0})
        counts["total"] += 1
        counts["first_try_correct"] += item.first_outcome in FIRST_TRY_RIGHT
    # an answer the learner overruled is theirs to judge, and an ordering is about a paragraph, not a word:
    # neither is listed as missed
    missed = [item for item in graded if _first_miss(item) and item.kind not in ("sentence_order", "shadow")]
    return {
        "items_total": len(graded),
        "answered": sum(1 for item in graded if _answered(item)),
        "first_try_correct": sum(1 for item in graded if item.first_outcome in FIRST_TRY_RIGHT),
        "fixed_on_retry": sum(1 for item in missed if item.attempts and item.attempts[-1]["outcome"] == "correct"),
        "skipped": sum(1 for item in graded if item.first_outcome == "skipped"
                       and item.attempts[0].get("skip") not in AUDIO_SKIPS),
        "overridden": sum(1 for item in graded if item.key.get("override")),
        "points_earned": sum(item.points_awarded for item in graded) + bonus,
        "session_bonus": bonus,
        "by_kind": by_kind,
        "missed": _once_per_ref(missed),
        "suggestions": [],
    }


def _once_per_ref(missed: list[ExerciseItem]) -> list[dict[str, Any]]:
    """What the summary lists as missed: a word missed in two items once, where it was first missed."""
    entries: dict[str, dict[str, Any]] = {}
    for item in missed:
        for entry in _missed(item):
            entries.setdefault(entry["ref"], entry)
    return list(entries.values())


# kinds whose miss is about knowing a word, so the word is offered for the word bank
SUGGEST_KINDS = frozenset({"choice", "cloze_choice", "cloze_typed", "typed_recall", "flashcard", "listen_choose",
                           "dictation"})


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
    graded = [item for item in rows if item.kind not in UNGRADED]
    if not early and any(not item.closed for item in graded):
        raise ExerciseError("answer or skip every item first, or finish early", 409)
    bonus = None
    answered = sum(1 for item in graded if _answered(item))
    if answered >= SESSION_BONUS_MIN_ITEMS:
        bonus = record_activity(session, learner_id, kind="exercise_session", ref=str(row.id), request_id=request_id,
                                meta={"items": answered})
    summary = {**_summary(rows, bonus.points if bonus else 0), "request_id": request_id}
    offered: list[tuple[str, dict[str, Any]]] = []
    for item in graded:
        if not _first_miss(item):
            continue
        if item.kind in SUGGEST_KINDS and item.word and "word" in item.key:
            if _word_missed(item, item.attempts[0]["response"]["feedback"] if item.attempts else None):
                offered.append((item.word, item.key["word"]))
        elif item.kind == "match_pairs" and item.attempts:
            pairs = item.attempts[0]["response"]["feedback"].get("pairs") or {}
            offered += [(item.key["words"][part], item.key["cards"][part]) for part, result in pairs.items()
                        if not result["ok"]]
    summary["suggestions"] = mistakes.suggest_words(session, learner_id, offered)
    completion = _completion(session, row, rows)
    if completion is not None:
        summary["completion"] = completion
    now = utcnow()
    row.summary, row.status, row.finished_at, row.updated_at = summary, "finished", now, now
    session.flush()
    return {"id": row.id, "status": "finished", "summary": summary, "points": bonus.points if bonus else 0,
            **reached(bonus)}


def _first_choice(item: ExerciseItem) -> int | None:
    """The authored option first chosen for a question (its place in the authored list); None for a skip."""
    first = item.attempts[0]
    option = None if first.get("skip") else first.get("answer", {}).get("option")
    return item.key["positions"].get(option) if option else None


def _completion(session: Session, row: ExerciseSession, rows: list[ExerciseItem]) -> dict[str, Any] | None:
    """What a topic or lesson session does for its activity (activities.py): the first answers to all of its
    questions count; a retry, a question never tried, a warm-up or content changed since the start do not."""
    if not row.skill:
        return None
    _inherit_reading_assistance(rows)
    questions = [item for item in rows if item.key.get("authored")]
    base = {"scope": "topic" if row.topic_id else "lesson", "skill": row.skill, "topic_id": row.topic_id or None,
            "to_retry": sum(1 for item in questions if item.first_outcome not in FIRST_TRY_RIGHT)}
    reason = None
    activity = None
    if row.skill not in activities.RECEPTIVE:
        reason = "open_task"
    elif row.params.get("retry"):
        reason = "retry"
    elif not questions or any(not item.attempts for item in questions):
        reason = "unfinished"
    elif any(item.hint_used for item in questions):
        reason = "assisted"
    else:
        try:
            activity = activities.activity_for(row.stage_id, topic_id=row.topic_id or None, skill=row.skill)
        except activities.ActivityNotFound:
            activity = None
        if activity is None or activity.content_version != row.content_version:
            reason = "content_changed"
    if reason is not None or activity is None:
        return {**base, "counted": False, "reason": reason,
                "completed": activities.stored_completion(session, learner_id=row.learner_id, stage_id=row.stage_id,
                                                          topic_id=row.topic_id, skill=row.skill)}
    chosen = {item.key["question"]: _first_choice(item) for item in questions}
    return {**base, **activities.record_result(session, learner_id=row.learner_id, session_id=row.id,
                                               activity=activity, chosen=chosen)}


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
                       "hint_used": item.hint_used, "overridden": bool(item.key.get("override")),
                       "points": item.points_awarded,
                       "attempts": [{"outcome": a["outcome"], "at": a["at"], "given": a.get("answer"),
                                     "skip": a.get("skip")} for a in item.attempts],
                       "overridden_at": item.key["override"]["at"] if item.key.get("override") else None,
                       # the learner's own report, without its request id
                       "report": {k: v for k, v in item.key["report"].items()
                                  if k not in ("request_id", "fingerprint")}
                       if item.key.get("report") else None,
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
