"""One conversation turn: learner utterance in, character reply out, everything persisted as evidence."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from dlp.config import Settings
from dlp.db.base import utcnow
from dlp.domains.content.schemas import CheckpointPayload, MissionDocument, SpeakingPayload, Step
from dlp.domains.content.service import get_mission, mission_document
from dlp.domains.practice.actions import AppointmentState, required_actions_completed
from dlp.domains.practice.models import EvidenceRecord, PracticeSession, PracticeTurn
from dlp.domains.practice.prompts import fixed_line
from dlp.domains.practice.service import PracticeError, record_evidence
from dlp.domains.practice.workflow import run_turn
from dlp.domains.progress.models import SkillRecord
from dlp.domains.speech.models import AudioAsset
from dlp.domains.usage import service as usage
from dlp.providers.base import ProviderError
from dlp.providers.registry import Providers

MODEL_CALLS_PER_TURN = 2
TOKENS_PER_TURN_ESTIMATE = 1800


@dataclass
class TurnOutcome:
    turn: PracticeTurn
    deduplicated: bool
    step_completed: bool
    appointment: dict[str, Any]
    reply_source: str


class TurnFailed(PracticeError):
    """The model did not answer. The failed turn row is kept so the failure is visible and countable."""

    def __init__(self, turn: PracticeTurn | None, cause: str = "") -> None:
        detail = "the conversation model did not answer; try again"
        if cause:
            detail = f"{detail} ({cause})"
        super().__init__(detail, status_code=502)
        self.turn = turn


def conversation_step(document: MissionDocument, practice: PracticeSession, step_key: str) -> Step:
    step = next((s for s in document.steps if s.key == step_key), None)
    if step is None:
        raise PracticeError("step not found", status_code=404)
    if not isinstance(step.payload, SpeakingPayload | CheckpointPayload):
        raise PracticeError("this step has no conversation", status_code=400)
    if step.variant != practice.variant:
        raise PracticeError(f"step {step_key} belongs to the {step.variant} variant, this session is {practice.variant}",
                            status_code=409)
    return step


def opening_line(document: MissionDocument, step: Step) -> str:
    scenario = document.scenario(step.payload.scenario_id)  # type: ignore[union-attr]
    return fixed_line(scenario, "opening", AppointmentState())


def existing_turn(session: Session, practice: PracticeSession, request_id: str) -> PracticeTurn | None:
    return session.scalar(
        select(PracticeTurn).where(PracticeTurn.session_id == practice.id, PracticeTurn.request_id == request_id)
    )


def turn_count_for(session: Session, practice: PracticeSession, step_key: str) -> int:
    """Turns that count against the step's limit: failed turns (no model answer) do not use up the budget."""
    return session.scalar(
        select(func.count()).select_from(PracticeTurn)
        .where(PracticeTurn.session_id == practice.id, PracticeTurn.step_key == step_key,
               PracticeTurn.status != "failed")
    ) or 0


def ensure_turn_allowed(session: Session, document: MissionDocument, practice: PracticeSession, step_key: str,
                        modality: str) -> Step:
    """Everything that can be refused before any provider is called. Raises PracticeError."""
    step = conversation_step(document, practice, step_key)
    payload = step.payload
    if practice.status != "active":
        raise PracticeError("this session is closed", status_code=409)
    if modality not in ("speech", "typed"):
        raise PracticeError("modality must be speech or typed", status_code=422)
    if isinstance(payload, CheckpointPayload) and modality == "typed" and not payload.restrictions.typed_fallback:
        raise PracticeError("typed input is not allowed in the checkpoint", status_code=403)
    if isinstance(payload, SpeakingPayload) and modality == "typed" and not payload.typed_fallback_allowed:
        raise PracticeError("typed input is not allowed in this step", status_code=403)
    if turn_count_for(session, practice, step_key) >= payload.max_turns:  # type: ignore[union-attr]
        raise PracticeError("the maximum number of turns for this step is reached", status_code=409)
    return step


def _history(practice: PracticeSession, step_key: str) -> list[tuple[str, str]]:
    history: list[tuple[str, str]] = []
    for turn in practice.turns:
        if turn.step_key != step_key or turn.status != "completed":
            continue
        history.append(("learner", turn.learner_text))
        if turn.character_text:
            history.append(("character", turn.character_text))
    return history


def _deduplicated(practice: PracticeSession, turn: PracticeTurn, required_actions: list[str]) -> TurnOutcome:
    if turn.status == "failed":
        raise TurnFailed(turn, str(turn.model_meta.get("error", "")))
    state = AppointmentState.from_dict(practice.state.get("appointment"))
    return TurnOutcome(turn, True, required_actions_completed(state, required_actions), state.as_dict(),
                       str(turn.model_meta.get("reply_source", "")))


def submit_turn(
    session: Session,
    settings: Settings,
    providers: Providers,
    *,
    practice: PracticeSession,
    step_key: str,
    modality: str,
    learner_text: str,
    request_id: str,
    learner_audio_asset_id: uuid.UUID | None = None,
    transcript_meta: dict[str, Any] | None = None,
) -> TurnOutcome:
    mission = get_mission(session, practice.mission_id)
    assert mission is not None
    document = mission_document(mission)
    step = conversation_step(document, practice, step_key)
    payload = step.payload
    scenario = document.scenario(payload.scenario_id)  # type: ignore[union-attr]

    # A retry with the same request id gets the same answer, even when that turn closed the session.
    existing = existing_turn(session, practice, request_id)
    if existing is not None:
        return _deduplicated(practice, existing, payload.required_actions)  # type: ignore[union-attr]

    ensure_turn_allowed(session, document, practice, step_key, modality)
    learner_text = learner_text.strip()
    if not learner_text:
        raise PracticeError("nothing to send", status_code=422)
    if len(learner_text) > 600:
        raise PracticeError("utterance too long", status_code=413)
    turn_count = turn_count_for(session, practice, step_key)

    # Reserve before the model is called; commit the measured usage afterwards, release on failure.
    calls_reservation = usage.reserve(session, settings, practice.learner_id, "model_calls", MODEL_CALLS_PER_TURN, request_id)
    tokens_reservation = usage.reserve(session, settings, practice.learner_id, "tokens", TOKENS_PER_TURN_ESTIMATE, request_id)

    last_index = session.scalar(select(func.max(PracticeTurn.turn_index)).where(PracticeTurn.session_id == practice.id))
    next_index = (last_index or 0) + 1
    turn = PracticeTurn(
        session_id=practice.id, turn_index=next_index, step_key=step_key, request_id=request_id, modality=modality,
        learner_text=learner_text, learner_audio_asset_id=learner_audio_asset_id, status="pending",
        model_meta={"transcript": transcript_meta or {}},
    )
    session.add(turn)
    session.flush()

    appointment_before = practice.state.get("appointment") or {}
    try:
        result = run_turn(
            providers.chat, scenario=scenario, appointment=appointment_before, history=_history(practice, step_key),
            learner_text=learner_text, request_id=request_id, max_output_tokens=min(settings.chat_max_output_tokens, 300),
        )
    except Exception as exc:  # noqa: BLE001 - the turn row records the failure; the client may retry with a new request id
        usage.release(session, calls_reservation.id)
        usage.release(session, tokens_reservation.id)
        turn.status = "failed"
        error = f"{exc.__class__.__name__}: {exc}"[:300]
        turn.model_meta = {**turn.model_meta, "error": error}
        session.flush()
        raise TurnFailed(turn, error) from exc

    calls = result.get("model_calls", [])
    usage.commit(session, calls_reservation.id, float(len(calls)))
    usage.commit(session, tokens_reservation.id, float(sum(c.get("input_tokens", 0) + c.get("output_tokens", 0) for c in calls)))

    turn.proposed_action = result["proposed"]
    turn.action_result = result["action_result"]
    turn.character_text = result["reply_nl"]
    turn.model_meta = {
        **turn.model_meta,
        "phase": result["phase"],
        "reply_source": result["reply_source"],
        "model_calls": calls,
        "errors": result.get("errors", []),
        "understood_nl": next((c.get("understood_nl", "") for c in calls if c.get("step") == "propose_action"), ""),
    }
    turn.status = "completed"

    state = AppointmentState.from_dict(result["appointment"])
    record_evidence(
        session, practice, step_key=step_key, skill=step.skill,
        kind="transcript" if modality == "speech" else "typed_text", modality=modality,
        payload={"text": learner_text, "turn_index": next_index,
                 "audio_asset_id": str(learner_audio_asset_id) if learner_audio_asset_id else None,
                 **({"stt": transcript_meta} if transcript_meta else {})},
        source=(transcript_meta or {}).get("provider", "application") if modality == "speech" else "learner",
        turn_id=turn.id,
    )
    record_evidence(
        session, practice, step_key=step_key, skill=step.skill, kind="action_result", modality="none",
        payload={"proposed": result["proposed"], "result": result["action_result"], "turn_index": next_index},
        source="application", turn_id=turn.id,
    )

    session.expire(practice, ["evidence"])  # the new records must be visible to the skill record update
    completed = required_actions_completed(state, payload.required_actions)  # type: ignore[union-attr]
    progress = dict(practice.state.get("step_progress") or {})
    modalities = sorted({modality, *progress.get(step_key, {}).get("modalities", [])})
    progress[step_key] = {"turns": turn_count + 1, "completed": completed, "modalities": modalities}
    practice.state = {**practice.state, "appointment": state.as_dict(), "step_progress": progress}
    practice.current_step_key = step_key
    practice.updated_at = utcnow()
    _update_skill_record(session, practice, step, completed, modality)
    if isinstance(payload, CheckpointPayload):
        if completed:
            practice.status = "completed"
            practice.completed_at = utcnow()
        elif turn_count + 1 >= payload.max_turns:
            # The only attempt is used up without the required actions: the session ends, the evidence stays.
            practice.status = "ended"
            practice.completed_at = utcnow()

    _attach_character_audio(session, settings, providers, practice, turn, request_id)
    session.flush()
    session.expire(practice, ["turns", "evidence"])
    return TurnOutcome(turn, False, completed, state.as_dict(), result["reply_source"])


def _update_skill_record(session: Session, practice: PracticeSession, step: Step, completed: bool, modality: str) -> None:
    record = session.scalar(
        select(SkillRecord).where(SkillRecord.learner_id == practice.learner_id, SkillRecord.mission_id == practice.mission_id,
                                  SkillRecord.skill == step.skill)
    )
    if record is None:
        return
    if record.status == "not_started":
        record.status = "in_progress"
        record.attempts = record.attempts + 1
    # Typed turns are labelled typed evidence and never count as speaking practice: the goal can be reached
    # with typed text, but the speaking record only moves on when at least one turn of the step was spoken.
    spoken = any(e.kind == "transcript" and e.step_key == step.key for e in practice.evidence)
    if completed and spoken:
        record.status = "checkpoint_passed" if step.payload.type == "checkpoint" else "practised"
    assessment = dict(record.latest_assessment or {})
    assessment[step.key] = {"completed": completed, "last_modality": modality, "session_id": str(practice.id),
                            "spoken": spoken, "typed_only": completed and not spoken}
    record.latest_assessment = assessment
    record.evidence_ids = [str(e.id) for e in practice.evidence if e.skill == step.skill][-50:]


def _attach_character_audio(session: Session, settings: Settings, providers: Providers, practice: PracticeSession,
                            turn: PracticeTurn, request_id: str) -> None:
    """Synthesise the reply. A synthesis failure never fails the turn: the text is still there."""
    if not turn.character_text:
        return
    reservation = None
    try:
        reservation = usage.reserve(session, settings, practice.learner_id, "audio_seconds",
                                    max(1.0, len(turn.character_text) / 14.0), f"{request_id}-tts")
        audio = providers.tts.synthesize(turn.character_text, request_id=request_id)
        seconds = _wav_seconds(audio.wav_bytes, audio.sample_rate)
        usage.commit(session, reservation.id, seconds)
        blob_key = f"synthesis/{practice.learner_id}/{request_id}.wav"
        providers.blob.put(blob_key, audio.wav_bytes, content_type="audio/wav")
        asset = AudioAsset(
            learner_id=practice.learner_id, kind="synthesis", blob_key=blob_key, container=settings.blob_container,
            source_container_format="wav", source_codec="pcm_s16le", source_bytes=len(audio.wav_bytes),
            duration_seconds=seconds, sample_rate=audio.sample_rate, channels=1, label=audio.label,
            provider=audio.provider, request_id=request_id, meta={"voice": audio.voice, "turn_id": str(turn.id)},
        )
        session.add(asset)
        session.flush()
        turn.character_audio_asset_id = asset.id
    except (ProviderError, usage.UsageLimitExceeded) as exc:
        if reservation is not None:
            usage.release(session, reservation.id)
        turn.model_meta = {**turn.model_meta, "audio_error": f"{exc.__class__.__name__}: {exc}"[:200]}


def _wav_seconds(wav_bytes: bytes, sample_rate: int) -> float:
    import io
    import wave

    try:
        with wave.open(io.BytesIO(wav_bytes), "rb") as handle:
            return handle.getnframes() / float(handle.getframerate() or sample_rate or 16000)
    except wave.Error:
        return max(0.1, len(wav_bytes) / float(2 * (sample_rate or 16000)))


def turn_view(turn: PracticeTurn) -> dict[str, Any]:
    meta = turn.model_meta or {}
    return {
        "id": str(turn.id),
        "turn_index": turn.turn_index,
        "step_key": turn.step_key,
        "request_id": turn.request_id,
        "modality": turn.modality,
        "learner_text": turn.learner_text,
        "learner_audio_asset_id": str(turn.learner_audio_asset_id) if turn.learner_audio_asset_id else None,
        "character_text": turn.character_text,
        "character_audio_asset_id": str(turn.character_audio_asset_id) if turn.character_audio_asset_id else None,
        "proposed_action": turn.proposed_action,
        "action_result": turn.action_result,
        "phase": meta.get("phase"),
        "reply_source": meta.get("reply_source"),
        "understood_nl": meta.get("understood_nl", ""),
        "model_calls": meta.get("model_calls", []),
        "errors": meta.get("errors", []),
        "error": meta.get("error"),
        "audio_error": meta.get("audio_error"),
        "status": turn.status,
        "created_at": turn.created_at.isoformat(),
    }


def evidence_view(record: EvidenceRecord) -> dict[str, Any]:
    return {
        "id": str(record.id), "turn_id": str(record.turn_id) if record.turn_id else None, "step_key": record.step_key,
        "skill": record.skill, "kind": record.kind, "modality": record.modality, "payload": record.payload,
        "source": record.source, "created_at": record.created_at.isoformat(),
    }
