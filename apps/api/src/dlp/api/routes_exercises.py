from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile
from sqlalchemy.orm import Session

from dlp.api.deps import RequestContext, context_dep, db_session, providers_dep, settings_dep
from dlp.api.routes_curriculum import _run
from dlp.config import Settings
from dlp.domains.exercises import service
from dlp.domains.exercises.schemas import (
    AnswerBody,
    AnswerResult,
    CreateBody,
    FinishBody,
    FinishResult,
    OverrideBody,
    ReportBody,
    ReportResult,
    SessionView,
    SkipBody,
)
from dlp.providers.registry import Providers

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.post("/sessions", response_model=SessionView, responses={201: {"model": SessionView}})
def create_session(body: CreateBody, response: Response, ctx: RequestContext = Depends(context_dep),
                   settings: Settings = Depends(settings_dep), session: Session = db_session):
    """Start (201), resume or replay (200) a practice session. No model call; the items are generated and stored."""
    def operation():
        row, found = service.create(session, settings, ctx.learner, body)
        if found == "created":
            response.status_code = 201
        return service.session_view(row, service.items(session, row), resumed=found == "resumed")
    return _run(operation)


@router.get("/sessions/{session_id}", response_model=SessionView)
def get_session_view(session_id: uuid.UUID, ctx: RequestContext = Depends(context_dep),
                     session: Session = db_session):
    def operation():
        row = service.get(session, ctx.learner.id, session_id)
        return service.session_view(row, service.items(session, row))
    return _run(operation)


@router.post("/sessions/{session_id}/items/{item_id}/answer", response_model=AnswerResult)
def answer_item(session_id: uuid.UUID, item_id: uuid.UUID, body: AnswerBody,
                ctx: RequestContext = Depends(context_dep), session: Session = db_session):
    return _run(lambda: service.respond(session, ctx.learner.id, session_id, item_id, request_id=body.request_id,
                                        answer=body.answer, hint_used=body.hint_used))


@router.post("/sessions/{session_id}/items/{item_id}/skip", response_model=AnswerResult)
def skip_item(session_id: uuid.UUID, item_id: uuid.UUID, body: SkipBody,
              ctx: RequestContext = Depends(context_dep), session: Session = db_session):
    return _run(lambda: service.respond(session, ctx.learner.id, session_id, item_id, request_id=body.request_id,
                                        skip=body.reason))


class WavResponse(Response):
    media_type = "audio/wav"


@router.post("/sessions/{session_id}/items/{item_id}/audio", response_class=WavResponse)
def item_audio(session_id: uuid.UUID, item_id: uuid.UUID, ctx: RequestContext = Depends(context_dep),
               settings: Settings = Depends(settings_dep), providers: Providers = Depends(providers_dep),
               session: Session = db_session):
    """The sound of an item with speech, from the speech cache; a sound already made costs no allowance."""
    def operation():
        wav, cached = service.item_audio(session, settings, learner_id=ctx.learner.id, session_id=session_id,
                                         item_id=item_id, request_id=ctx.request_id, tts=providers.tts,
                                         blob=providers.blob)
        return WavResponse(content=wav, headers={"X-Audio-Cached": "1" if cached else "0",
                                                 "X-Audio-Label": providers.tts.label,
                                                 "X-Audio-Voice": providers.tts.voice, "Cache-Control": "no-store"})
    return _run(operation)


@router.post("/sessions/{session_id}/items/{item_id}/recording", response_model=AnswerResult)
def record_item(session_id: uuid.UUID, item_id: uuid.UUID,
                request_id: str = Form(min_length=8, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$"),
                audio: UploadFile = File(...), ctx: RequestContext = Depends(context_dep),
                settings: Settings = Depends(settings_dep), providers: Providers = Depends(providers_dep),
                session: Session = db_session):
    """A shadowing attempt: heard or not heard, never a score; the recording is not kept."""
    return _run(lambda: service.record(
        session, settings, learner_id=ctx.learner.id, session_id=session_id, item_id=item_id, request_id=request_id,
        upload_bytes=audio.file.read(settings.max_upload_bytes + 1), upload_filename=audio.filename or "recording",
        stt=providers.stt, blob=providers.blob))


@router.post("/sessions/{session_id}/items/{item_id}/override", response_model=AnswerResult)
def override_item(session_id: uuid.UUID, item_id: uuid.UUID, body: OverrideBody,
                  ctx: RequestContext = Depends(context_dep), session: Session = db_session):
    """"Mijn antwoord klopt ook" on a typed answer or a built sentence; it never completes anything."""
    return _run(lambda: service.override(session, ctx.learner.id, session_id, item_id, request_id=body.request_id))


@router.post("/sessions/{session_id}/items/{item_id}/report", response_model=ReportResult)
def report_item(session_id: uuid.UUID, item_id: uuid.UUID, body: ReportBody,
                ctx: RequestContext = Depends(context_dep), session: Session = db_session):
    """"Meld een probleem": kept with the item for the content review; it changes nothing in the session."""
    return _run(lambda: service.report(session, ctx.learner.id, session_id, item_id, request_id=body.request_id,
                                       reason=body.reason, note=body.note))


@router.post("/sessions/{session_id}/finish", response_model=FinishResult)
def finish_session(session_id: uuid.UUID, body: FinishBody, ctx: RequestContext = Depends(context_dep),
                   session: Session = db_session):
    return _run(lambda: service.finish(session, ctx.learner.id, session_id, request_id=body.request_id,
                                       early=body.early))
