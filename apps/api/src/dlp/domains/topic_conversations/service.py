from __future__ import annotations

import hashlib
import json
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from dlp.config import Settings
from dlp.db.base import utcnow
from dlp.domains.curriculum.service import CurriculumError, localized, recording, word_count
from dlp.domains.curriculum.topics import topic_for, topics_for
from dlp.domains.identity.models import Learner
from dlp.domains.topic_conversations.content import bank, blueprint_for
from dlp.domains.topic_conversations.models import TopicConversation
from dlp.domains.topic_conversations.schemas import Blueprint
from dlp.domains.topic_conversations.workflow import messages_for, reservation_tokens, run_turn
from dlp.domains.usage import service as usage
from dlp.providers.base import ProviderError
from dlp.providers.registry import Providers

MAX_TURNS = 6
MAX_ACTIVE = 3
MAX_DAILY_STARTS = 20


def _policy(settings: Settings) -> dict:
    return {"max_turns": MAX_TURNS, "recording_max_seconds": min(60, settings.max_audio_seconds),
            "min_words": 1, "max_words": 100, "max_text_length": 2000}


def listing(session: Session, learner_id: uuid.UUID, stage_id: str | None) -> dict:
    from dlp.domains.curriculum.schemas import STAGE_IDS
    if stage_id is not None and stage_id not in STAGE_IDS:
        raise CurriculumError("learning stage not found", 404)
    active = {item.blueprint_id: str(item.id) for item in session.scalars(select(TopicConversation).where(
        TopicConversation.learner_id == learner_id, TopicConversation.status == "active"))}
    return {"learner_key": str(learner_id), "items": [{
        "id": item.id, "stage_id": item.stage_id, "topic_id": item.topic_id,
        "title": item.title.model_dump(), "role": item.role.model_dump(), "active_session_id": active.get(item.id),
    } for item in bank().conversations if stage_id is None or item.stage_id == stage_id]}


def blueprint_view(item: Blueprint, settings: Settings) -> dict:
    return {**item.model_dump(include={"id", "stage_id", "topic_id", "title", "role", "setup", "opening"}),
            "goals": [step.goal.model_dump() for step in item.steps], "review_status": "unreviewed", **_policy(settings)}


def _fully_assessed(row: TopicConversation) -> bool:
    responses = [turn for turn in row.history if turn["action"] == "respond"]
    return bool(responses) and all(turn.get("assessed") is True for turn in responses)


def _summary(row: TopicConversation, item: Blueprint) -> dict | None:
    if row.status == "active":
        return None
    if not _fully_assessed(row):
        return localized(
            "Deze oefenbeurt is niet inhoudelijk beoordeeld. U kunt het gesprek opnieuw oefenen; "
            "hieruit wordt geen oordeel over uw vaardigheden afgeleid.",
            "This practice conversation was not assessed. You can practise it again; "
            "no conclusion about your skills is drawn from it.",
            "این مکالمهٔ تمرینی از نظر محتوایی ارزیابی نشده است. می‌توانید دوباره تمرین کنید؛ "
            "از آن دربارهٔ مهارت‌های شما نتیجه‌گیری نمی‌شود.",
        )
    met, total = row.step_index, len(item.steps)
    return localized(
        f"{met} van {total} gespreksdoelen bereikt. Bekijk de doelen en oefen opnieuw wat nog niet lukte. "
        "Dit is oefenfeedback, geen niveau- of uitspraakbeoordeling.",
        f"{met} of {total} conversation goals reached. Review the goals and retry what still needs practice. "
        "This is practice feedback, not a level or pronunciation assessment.",
        f"{met} هدف از {total} هدف مکالمه انجام شد. هدف‌ها را مرور کنید و موارد باقی‌مانده را دوباره تمرین کنید. "
        "این بازخورد تمرینی است، نه ارزیابی سطح یا تلفظ.",
    )


def view(row: TopicConversation, settings: Settings) -> dict:
    item = Blueprint.model_validate(row.blueprint)
    history = [{key: turn[key] for key in ("id", "number", "action", "learner_text", "reply", "accepted", "assisted", "mode")}
               for turn in row.history]
    return {"id": str(row.id), "blueprint_id": row.blueprint_id, "stage_id": row.stage_id, "topic_id": row.topic_id,
            "title": item.title.model_dump(), "role": item.role.model_dump(), "setup": item.setup.model_dump(),
            "opening": item.opening.model_dump(), "mode": row.mode, "status": row.status,
            "turn_count": len(row.history), "history": history, "learner_key": str(row.learner_id),
            "current_goal": item.steps[row.step_index].goal.model_dump() if row.status == "active" else None,
            "goals": [{"goal": step.goal.model_dump(), "met": index < row.step_index,
                       "assisted": step.id in row.assisted_steps} for index, step in enumerate(item.steps)],
            "summary": _summary(row, item), "review_status": "unreviewed", **_policy(settings)}


def get(session: Session, learner_id: uuid.UUID, conversation_id: uuid.UUID, *, lock: bool = False) -> TopicConversation:
    query = select(TopicConversation).where(TopicConversation.id == conversation_id,
                                           TopicConversation.learner_id == learner_id)
    if lock:
        query = query.with_for_update(nowait=True).execution_options(populate_existing=True)
    row = session.scalar(query)
    if row is None:
        raise CurriculumError("conversation not found", 404)
    return row


def start(session: Session, learner_id: uuid.UUID, *, blueprint_id: str, request_id: str, mode: str) -> TopicConversation:
    item = blueprint_for(blueprint_id)
    # Serialise starts for this learner so concurrent tabs cannot exceed session limits.
    session.scalar(select(Learner).where(Learner.id == learner_id).with_for_update(nowait=True))
    previous = session.scalar(select(TopicConversation).where(TopicConversation.learner_id == learner_id,
                                                              TopicConversation.request_id == request_id))
    if previous is not None:
        if previous.blueprint_id != blueprint_id or previous.mode != mode:
            raise CurriculumError("this start identifier belongs to a different conversation", 409)
        return previous
    active = list(session.scalars(select(TopicConversation).where(TopicConversation.learner_id == learner_id,
                                                                 TopicConversation.status == "active")))
    if any(row.blueprint_id == blueprint_id for row in active):
        raise CurriculumError("resume or finish the active conversation for this topic before starting another", 409)
    if len(active) >= MAX_ACTIVE:
        raise CurriculumError("finish one of your active conversations before starting another", 429)
    since = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    count = session.scalar(select(func.count()).select_from(TopicConversation).where(
        TopicConversation.learner_id == learner_id, TopicConversation.created_at >= since))
    if count >= MAX_DAILY_STARTS:
        raise CurriculumError("today's conversation limit is reached; resume a conversation or try tomorrow", 429)
    topic = topic_for(topics_for(item.stage_id), item.topic_id)
    topic_version = hashlib.sha256(topic.model_dump_json().encode()).hexdigest()
    row = TopicConversation(learner_id=learner_id, request_id=request_id, blueprint_id=item.id,
                            stage_id=item.stage_id, topic_id=item.topic_id, mode=mode, topic_content_version=topic_version,
                            blueprint=item.model_dump(), history=[], assisted_steps=[], step_index=0, status="active")
    session.add(row)
    session.flush()
    return row


def _record_episode(session: Session, row: TopicConversation):
    if not any(turn["action"] == "respond" for turn in row.history):
        return  # Opening or requesting help does not establish a performance observation.
    from dlp.domains.coaching.service import record_observation
    item = Blueprint.model_validate(row.blueprint)
    assessed = _fully_assessed(row)
    passed = (True if row.status == "completed" else False if len(row.history) == MAX_TURNS else None) if assessed else None
    record_observation(
        session, learner_id=row.learner_id, stage_id=row.stage_id, topic_id=row.topic_id,
        skill="speaking" if row.mode == "spoken" else "writing", source="conversation",
        request_id="conversation-" + str(row.id), content_version=hashlib.sha256(item.model_dump_json().encode()).hexdigest(),
        passed=passed,
        summary={"assessed": assessed, "assisted": bool(row.assisted_steps), "goals_met": row.step_index,
                 "goals_total": len(item.steps), "input_mode": row.mode,
                 "topic_content_version": row.topic_content_version},
        failed_refs=[step.id for step in item.steps[row.step_index:]] if assessed else [],
        payload={"conversation_id": str(row.id), "mode": row.mode, "history": row.history},
    )


def finish(session: Session, row: TopicConversation) -> TopicConversation:
    if row.status == "active":
        row.status = "ended"
        row.updated_at = utcnow()
        _record_episode(session, row)
        session.flush()
    return row


def turn(session: Session, settings: Settings, providers: Providers, row: TopicConversation, *,
         client_turn_id: str, expected_turn: int, action: str, text: str, audio_asset_id: uuid.UUID | None,
         request_id: str) -> TopicConversation:
    submission = {"expected_turn": expected_turn, "action": action, "text": text,
                  "audio_asset_id": str(audio_asset_id) if audio_asset_id else None}
    fingerprint = hashlib.sha256(json.dumps(submission, sort_keys=True).encode()).hexdigest()
    previous = next((item for item in row.history if item["id"] == client_turn_id), None)
    if previous is not None:
        if previous["fingerprint"] != fingerprint:
            raise CurriculumError("this turn identifier was already used for a different response", 409)
        return row  # Retrying after later turns returns current canonical state, without another call.
    if row.status != "active":
        raise CurriculumError("this conversation has finished; start a new practice conversation", 409)
    if expected_turn != len(row.history):
        raise CurriculumError("the conversation changed in another request; reload it before replying", 409)
    if len(row.history) >= MAX_TURNS:
        raise CurriculumError("this conversation has reached its turn limit", 409)
    item = Blueprint.model_validate(row.blueprint)
    step = item.steps[row.step_index]
    accepted = False
    assisted = False
    assessed = False
    if action != "respond":
        if text.strip() or audio_asset_id:
            raise CurriculumError("a help request must not contain a learner response", 422)
        learner_text = ""
        reply = (step.hint if action == "hint" else step.cue).model_dump()
        assisted = True
    else:
        if row.mode == "spoken":
            if audio_asset_id is None or text.strip():
                raise CurriculumError("submit your own new recording without a replacement transcript", 422)
            asset = recording(session, row.learner_id, audio_asset_id, after=row.created_at)
            if asset.duration_seconds > min(60, settings.max_audio_seconds):
                raise CurriculumError("record a shorter response within the recording time limit", 422)
            if any(entry.get("audio_asset_id") == str(audio_asset_id) for entry in row.history):
                raise CurriculumError("record a new response for this conversation turn", 422)
            learner_text = str(asset.meta["transcript"]).strip()
        else:
            if audio_asset_id:
                raise CurriculumError("typed conversation accepts typed responses only", 422)
            learner_text = text.strip()
        if len(learner_text) > 2000 or not 1 <= word_count(learner_text) <= 100:
            raise CurriculumError("use between 1 and 100 words, at most 2000 characters, for this turn", 422)
        if settings.chat_provider == "azure" and not settings.paid_usage_enabled:
            raise CurriculumError("Paid conversation practice is not enabled. "
                                  "Ask the owner to enable the practice allowance.", 403)
        from dlp.domains.coaching.service import paid_model_guard
        paid_model_guard(session, row.learner_id)
        estimate = reservation_tokens(messages_for(item, step, learner_text, row.history))
        call_id = uuid.uuid4().hex
        calls = usage.reserve(session, settings, row.learner_id, "model_calls", 1, call_id)
        try:
            tokens = usage.reserve(session, settings, row.learner_id, "tokens", estimate, call_id)
        except usage.UsageLimitExceeded:
            usage.release(session, calls.id)
            raise
        try:
            outcome = run_turn(providers.chat, blueprint=item, step_index=row.step_index, text=learner_text,
                               history=row.history, request_id=request_id)
        except ProviderError:
            # A timeout or malformed reply may still have been billed. Keep a conservative allowance charge;
            # the turn itself stays unmodified and the learner can retry the same turn identifier.
            usage.commit(session, calls.id, 1)
            usage.commit(session, tokens.id, estimate)
            raise
        usage.commit(session, calls.id, 1)
        usage.commit(session, tokens.id, outcome["tokens"])
        assessed = providers.chat.name != "fixture" and (row.mode == "typed" or asset.provider not in ("", "fixture"))
        accepted, reply = outcome["accepted"], outcome["reply"]
        assisted = bool(outcome["help_kind"])
    if assisted:
        row.assisted_steps = sorted(set(row.assisted_steps) | {step.id})
    row.history = [*row.history, {
        "id": client_turn_id, "number": len(row.history) + 1, "action": action, "learner_text": learner_text,
        "reply": reply, "accepted": accepted, "assisted": assisted or step.id in row.assisted_steps,
        "mode": row.mode, "goal_id": step.id, "fingerprint": fingerprint, "assessed": assessed,
        "audio_asset_id": str(audio_asset_id) if audio_asset_id else None,
    }]
    if accepted:
        row.step_index += 1
    if row.step_index == len(item.steps):
        row.status = "completed"
    elif len(row.history) == MAX_TURNS:
        row.status = "ended"
    row.updated_at = utcnow()
    if row.status != "active":
        _record_episode(session, row)
    session.flush()
    return row
