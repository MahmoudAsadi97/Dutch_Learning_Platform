from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from dlp.api.deps import RequestContext, context_dep, providers_dep, settings_dep
from dlp.config import Settings
from dlp.db.session import get_session
from dlp.domains.content.schemas import CheckpointPayload, MissionDocument, SpeakingPayload
from dlp.domains.content.service import get_mission, mission_document
from dlp.domains.feedback.service import generate_feedback, report_view, reports_for
from dlp.domains.practice.models import PracticeSession, PracticeTurn
from dlp.domains.practice.service import (
    PracticeError,
    abandon_session,
    get_session_for_learner,
    list_sessions,
    start_session,
)
from dlp.domains.practice.steps import record_help_use, save_draft, submit_answer, submit_writing
from dlp.domains.practice.turns import (
    TurnFailed,
    TurnOutcome,
    ensure_turn_allowed,
    evidence_view,
    existing_turn,
    opening_line,
    submit_turn,
    turn_view,
)
from dlp.domains.progress.service import ensure_skill_records
from dlp.domains.speech.audio import AudioError
from dlp.domains.speech.models import AudioAsset
from dlp.domains.speech.service import transcribe_upload
from dlp.domains.usage.service import UsageLimitExceeded
from dlp.providers.base import ProviderError, ProviderUnavailable
from dlp.providers.registry import Providers

router = APIRouter(prefix="/practice", tags=["practice"])


class StartSessionRequest(BaseModel):
    mission_id: str = Field(pattern=r"^[a-z0-9-]+$")
    variant: str = Field(default="base", pattern=r"^(base|transfer)$")


class TypedTurnRequest(BaseModel):
    step_key: str = Field(pattern=r"^[a-z0-9_-]+$")
    text: str = Field(min_length=1, max_length=600)


class AnswerRequest(BaseModel):
    step_key: str = Field(pattern=r"^[a-z0-9_-]+$")
    question_id: str = Field(pattern=r"^[a-z0-9_-]+$")
    chosen_index: int = Field(ge=0, le=10)


class HelpUseRequest(BaseModel):
    step_key: str = Field(pattern=r"^[a-z0-9_-]+$")
    level: int = Field(ge=1, le=3)
    kind: str = Field(pattern=r"^(hint_nl|gloss_fa|translation_fa|reading_translation|listening_transcript)$")
    question_id: str = Field(default="", pattern=r"^[a-z0-9_-]*$")


class DraftRequest(BaseModel):
    text: str = Field(max_length=4000)


class WritingRequest(BaseModel):
    step_key: str = Field(pattern=r"^[a-z0-9_-]+$")
    text: str = Field(min_length=1, max_length=4000)


class FeedbackRequest(BaseModel):
    step_key: str = Field(pattern=r"^[a-z0-9_-]+$")


def _session_view(practice: PracticeSession) -> dict[str, Any]:
    return {
        "id": str(practice.id),
        "mission_id": practice.mission_id,
        "variant": practice.variant,
        "status": practice.status,
        "current_step_key": practice.current_step_key,
        "request_id": practice.request_id,
        "state": practice.state,
        "appointment": practice.state.get("appointment") or {},
        "step_progress": practice.state.get("step_progress") or {},
        "started_at": practice.started_at.isoformat(),
        "updated_at": practice.updated_at.isoformat(),
        "completed_at": practice.completed_at.isoformat() if practice.completed_at else None,
        "turn_count": len(practice.turns),
        "evidence_count": len(practice.evidence),
    }


def _conversation_steps(document: MissionDocument, practice: PracticeSession) -> list[dict[str, Any]]:
    """What the client needs to run each conversation step of this variant: opening line, character, limits, rules."""
    items: list[dict[str, Any]] = []
    for step in document.steps:
        if step.variant != practice.variant or not isinstance(step.payload, SpeakingPayload | CheckpointPayload):
            continue
        scenario = document.scenario(step.payload.scenario_id)
        checkpoint = isinstance(step.payload, CheckpointPayload)
        restrictions = step.payload.restrictions if checkpoint else None
        items.append({
            "step_key": step.key,
            "scenario_kind": scenario.kind,
            "choices": [{"id": c.id, "label": c.label.model_dump()} for c in scenario.choices],
            "type": step.payload.type,
            "opening_line": opening_line(document, step),
            "character": {"name": scenario.character.name, "role": scenario.character.role.model_dump(),
                          "register": scenario.character.register_style},
            "goal": step.payload.goal.model_dump(),
            "required_actions": list(step.payload.required_actions),
            "max_turns": step.payload.max_turns,
            "typed_allowed": restrictions.typed_fallback if restrictions else step.payload.typed_fallback_allowed,  # type: ignore[union-attr]
            "help_allowed": restrictions.help_ladder if restrictions else True,
            "retry_allowed": restrictions.retry if restrictions else True,
            "slots": [{"id": s.id, "day": s.day.isoformat(), "start": s.start.isoformat(timespec="minutes")}
                      for s in scenario.available_slots],
        })
    return items


def _full_view(session: Session, practice: PracticeSession, request_id: str) -> dict[str, Any]:
    mission = get_mission(session, practice.mission_id)
    assert mission is not None
    document = mission_document(mission)
    return {
        "session": _session_view(practice),
        "conversation": _conversation_steps(document, practice),
        "turns": [turn_view(t) for t in practice.turns],
        "evidence": [evidence_view(e) for e in practice.evidence],
        "drafts": practice.state.get("drafts") or {},
        "feedback": [report_view(r) for r in reports_for(session, practice)],
        "request_id": request_id,
    }


def _turn_response(practice: PracticeSession, outcome: TurnOutcome, request_id: str) -> dict[str, Any]:
    return {
        "turn": turn_view(outcome.turn),
        "deduplicated": outcome.deduplicated,
        "step_completed": outcome.step_completed,
        "appointment": outcome.appointment,
        "reply_source": outcome.reply_source,
        "session": _session_view(practice),
        "request_id": request_id,
    }


def _failed_turn_response(exc: TurnFailed, practice: PracticeSession, request_id: str) -> JSONResponse:
    # Returned, not raised: the request's transaction must commit so the failed turn and the released usage persist.
    return JSONResponse(
        status_code=502,
        content={"detail": exc.reason, "turn": turn_view(exc.turn) if exc.turn is not None else None,
                 "session": _session_view(practice), "request_id": request_id},
        headers={"X-Request-Id": request_id},
    )


def _load(session: Session, ctx: RequestContext, session_id: uuid.UUID, *, for_update: bool = True) -> PracticeSession:
    try:
        return get_session_for_learner(session, ctx.learner.id, session_id, for_update=for_update)
    except PracticeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.reason) from exc


@router.post("/sessions", status_code=201)
def create(body: StartSessionRequest, ctx: RequestContext = Depends(context_dep),
           session: Session = Depends(get_session)) -> dict:
    mission = get_mission(session, body.mission_id)
    if mission is None:
        raise HTTPException(status_code=404, detail="mission not found")
    ensure_skill_records(session, ctx.learner.id, mission.id)
    try:
        practice = start_session(session, learner_id=ctx.learner.id, mission=mission, variant=body.variant,
                                 request_id=ctx.request_id)
    except PracticeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.reason) from exc
    return _full_view(session, practice, ctx.request_id)


@router.get("/sessions")
def index(
    mission_id: str | None = Query(default=None, pattern=r"^[a-z0-9-]+$"),
    variant: str | None = Query(default=None, pattern=r"^(base|transfer)$"),
    status: str | None = Query(default=None, pattern=r"^(active|completed|ended|abandoned)$"),
    ctx: RequestContext = Depends(context_dep),
    session: Session = Depends(get_session),
) -> dict:
    sessions = list_sessions(session, ctx.learner.id, mission_id=mission_id, variant=variant, status=status)
    return {"sessions": [_session_view(p) for p in sessions], "request_id": ctx.request_id}


@router.get("/sessions/{session_id}")
def show(session_id: uuid.UUID, ctx: RequestContext = Depends(context_dep),
         session: Session = Depends(get_session)) -> dict:
    practice = _load(session, ctx, session_id, for_update=False)
    return _full_view(session, practice, ctx.request_id)


@router.post("/sessions/{session_id}/abandon")
def abandon(session_id: uuid.UUID, ctx: RequestContext = Depends(context_dep),
            session: Session = Depends(get_session)) -> dict:
    practice = _load(session, ctx, session_id)
    try:
        abandon_session(session, practice)
    except PracticeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.reason) from exc
    return {"session": _session_view(practice), "request_id": ctx.request_id}


@router.post("/sessions/{session_id}/turns")
def typed_turn(
    session_id: uuid.UUID,
    body: TypedTurnRequest,
    ctx: RequestContext = Depends(context_dep),
    settings: Settings = Depends(settings_dep),
    providers: Providers = Depends(providers_dep),
    session: Session = Depends(get_session),
) -> Any:
    """A typed learner turn. Typed text is labelled as such in the evidence; the checkpoint refuses it."""
    practice = _load(session, ctx, session_id)
    try:
        outcome = submit_turn(session, settings, providers, practice=practice, step_key=body.step_key, modality="typed",
                              learner_text=body.text, request_id=ctx.request_id)
    except TurnFailed as exc:
        return _failed_turn_response(exc, practice, ctx.request_id)
    except UsageLimitExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except PracticeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.reason) from exc
    return _turn_response(practice, outcome, ctx.request_id)


@router.post("/sessions/{session_id}/turns/speech")
def speech_turn(
    session_id: uuid.UUID,
    audio: UploadFile = File(...),
    step_key: str = Form(pattern=r"^[a-z0-9_-]+$"),
    ctx: RequestContext = Depends(context_dep),
    settings: Settings = Depends(settings_dep),
    providers: Providers = Depends(providers_dep),
    session: Session = Depends(get_session),
) -> Any:
    """A spoken learner turn: upload → canonical WAV → transcript → the same turn workflow as typed input."""
    practice = _load(session, ctx, session_id)
    mission = get_mission(session, practice.mission_id)
    assert mission is not None
    document = mission_document(mission)
    repeated = existing_turn(session, practice, ctx.request_id) is not None
    try:
        if not repeated:
            ensure_turn_allowed(session, document, practice, step_key, "speech")
    except PracticeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.reason) from exc

    data = audio.file.read(settings.max_upload_bytes + 1)
    transcript_meta: dict[str, Any] = {}
    asset_id: uuid.UUID | None = None
    learner_text = ""
    if not repeated:  # a retry of a turn that already exists is answered from the stored turn, without a new transcription
        try:
            transcription = transcribe_upload(
                session, settings, learner_id=ctx.learner.id, request_id=ctx.request_id, upload_bytes=data,
                upload_filename=audio.filename or "", stt=providers.stt, blob=providers.blob, keep_recording=True,
            )
        except AudioError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.reason) from exc
        except UsageLimitExceeded as exc:
            raise HTTPException(status_code=429, detail=str(exc)) from exc
        except ProviderUnavailable as exc:
            raise HTTPException(status_code=503, detail=f"speech-to-text unavailable: {exc}") from exc
        except ProviderError as exc:
            raise HTTPException(status_code=502, detail=f"speech-to-text failed: {exc}") from exc
        learner_text = transcription.transcript.text.strip()
        if not learner_text:
            return _speech_error(422, "nothing was recognised in the recording; try again", ctx.request_id)
        asset_id = transcription.asset.id
        transcript_meta = {
            "provider": transcription.transcript.provider, "model": transcription.transcript.model,
            "language": transcription.transcript.language, "latency_ms": transcription.transcript.latency_ms,
            "duration_seconds": transcription.canonical.duration_seconds,
            "segments": [s.__dict__ for s in transcription.transcript.segments],
            "recording_stored": bool(transcription.asset.meta.get("stored")),
            "storage_warning": transcription.asset.meta.get("storage_warning"),
        }
    try:
        outcome = submit_turn(session, settings, providers, practice=practice, step_key=step_key, modality="speech",
                              learner_text=learner_text, request_id=ctx.request_id, learner_audio_asset_id=asset_id,
                              transcript_meta=transcript_meta)
    except TurnFailed as exc:
        return _failed_turn_response(exc, practice, ctx.request_id)
    except UsageLimitExceeded as exc:
        return _speech_error(429, str(exc), ctx.request_id)
    except PracticeError as exc:
        return _speech_error(exc.status_code, exc.reason, ctx.request_id)
    return _turn_response(practice, outcome, ctx.request_id)


def _speech_error(status: int, detail: str, request_id: str) -> JSONResponse:
    # A successful STT call has already consumed audio allowance. Return an error response
    # without rolling that transaction back when the later model step cannot start.
    return JSONResponse(status_code=status, content={"detail": detail, "request_id": request_id})


@router.get("/sessions/{session_id}/turns/{turn_id}/audio")
def character_audio(
    session_id: uuid.UUID,
    turn_id: uuid.UUID,
    ctx: RequestContext = Depends(context_dep),
    providers: Providers = Depends(providers_dep),
    session: Session = Depends(get_session),
) -> Response:
    """The synthesised character line for one turn, labelled as synthetic audio."""
    practice = _load(session, ctx, session_id)
    turn = session.get(PracticeTurn, turn_id)
    if turn is None or turn.session_id != practice.id:
        raise HTTPException(status_code=404, detail="turn not found")
    if turn.character_audio_asset_id is None:
        raise HTTPException(status_code=404, detail="this turn has no character audio")
    asset = session.get(AudioAsset, turn.character_audio_asset_id)
    if asset is None or asset.learner_id != ctx.learner.id:
        raise HTTPException(status_code=404, detail="audio not found")
    try:
        wav_bytes = providers.blob.get(asset.blob_key)
    except ProviderError as exc:
        raise HTTPException(status_code=404, detail="audio no longer stored") from exc
    headers = {
        "X-Audio-Label": asset.label,
        "X-Audio-Voice": str((asset.meta or {}).get("voice", "")),
        "X-Request-Id": ctx.request_id,
        "Cache-Control": "private, max-age=3600",
    }
    return Response(content=wav_bytes, media_type="audio/wav", headers=headers)


@router.post("/sessions/{session_id}/answers")
def answer(session_id: uuid.UUID, body: AnswerRequest, ctx: RequestContext = Depends(context_dep),
           session: Session = Depends(get_session)) -> dict:
    """An answer to a reading or listening question; correctness is decided here and stored as evidence."""
    practice = _load(session, ctx, session_id)
    try:
        outcome = submit_answer(session, practice, step_key=body.step_key, question_id=body.question_id,
                                chosen_index=body.chosen_index)
    except PracticeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.reason) from exc
    return {
        "evidence": evidence_view(outcome.evidence), "correct": outcome.correct, "answer_index": outcome.answer_index,
        "step_completed": outcome.step_completed, "answered": outcome.answered,
        "session": _session_view(practice), "request_id": ctx.request_id,
    }


@router.post("/sessions/{session_id}/help")
def help_used(session_id: uuid.UUID, body: HelpUseRequest, ctx: RequestContext = Depends(context_dep),
              session: Session = Depends(get_session)) -> dict:
    """One rung of the Persian help ladder was opened; recorded as evidence so feedback can see it."""
    practice = _load(session, ctx, session_id)
    try:
        evidence = record_help_use(session, practice, step_key=body.step_key, level=body.level, kind=body.kind,
                                   question_id=body.question_id)
    except PracticeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.reason) from exc
    return {"evidence": evidence_view(evidence), "session": _session_view(practice), "request_id": ctx.request_id}


@router.put("/sessions/{session_id}/drafts/{step_key}")
def draft(session_id: uuid.UUID, step_key: str, body: DraftRequest, ctx: RequestContext = Depends(context_dep),
          session: Session = Depends(get_session)) -> dict:
    """Autosave of the writing step; not evidence until the message is submitted."""
    practice = _load(session, ctx, session_id)
    try:
        entry = save_draft(session, practice, step_key=step_key, text=body.text)
    except PracticeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.reason) from exc
    return {"draft": entry, "request_id": ctx.request_id}


@router.post("/sessions/{session_id}/writing")
def writing(session_id: uuid.UUID, body: WritingRequest, ctx: RequestContext = Depends(context_dep),
            session: Session = Depends(get_session)) -> dict:
    """The submitted message of the writing step, stored as typed evidence with its word count."""
    practice = _load(session, ctx, session_id)
    try:
        outcome = submit_writing(session, practice, step_key=body.step_key, text=body.text)
    except PracticeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.reason) from exc
    return {
        "evidence": evidence_view(outcome.evidence), "word_count": outcome.word_count, "missing": outcome.missing,
        "step_completed": outcome.step_completed, "session": _session_view(practice), "request_id": ctx.request_id,
    }


@router.post("/sessions/{session_id}/feedback")
def feedback(
    session_id: uuid.UUID,
    body: FeedbackRequest,
    ctx: RequestContext = Depends(context_dep),
    settings: Settings = Depends(settings_dep),
    providers: Providers = Depends(providers_dep),
    session: Session = Depends(get_session),
) -> dict:
    """Feedback on one step, every point tied to evidence ids that were verified before storing."""
    practice = _load(session, ctx, session_id)
    try:
        report = generate_feedback(session, settings, providers, practice=practice, step_key=body.step_key,
                                   request_id=ctx.request_id)
    except UsageLimitExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except PracticeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.reason) from exc
    except ProviderUnavailable as exc:
        raise HTTPException(status_code=503, detail=f"feedback model unavailable: {exc}") from exc
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=f"feedback model failed: {exc}") from exc
    return {"report": report_view(report), "request_id": ctx.request_id}


@router.get("/sessions/{session_id}/feedback")
def feedback_index(session_id: uuid.UUID, ctx: RequestContext = Depends(context_dep),
                   session: Session = Depends(get_session)) -> dict:
    practice = _load(session, ctx, session_id, for_update=False)
    return {"reports": [report_view(r) for r in reports_for(session, practice)], "request_id": ctx.request_id}
