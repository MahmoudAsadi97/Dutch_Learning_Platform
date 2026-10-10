from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from dlp.api.deps import RequestContext, context_dep
from dlp.api.routes_curriculum import _run
from dlp.db.session import get_session
from dlp.domains.exercises import service
from dlp.domains.exercises.schemas import (
    AnswerBody,
    AnswerResult,
    CreateBody,
    FinishBody,
    FinishResult,
    SessionView,
    SkipBody,
)

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.post("/sessions", response_model=SessionView, responses={201: {"model": SessionView}})
def create_session(body: CreateBody, response: Response, ctx: RequestContext = Depends(context_dep),
                   session: Session = Depends(get_session)):
    """Start (201), resume or replay (200) a practice session. No model call; the items are generated and stored."""
    def operation():
        row, found = service.create(session, ctx.learner, body)
        if found == "created":
            response.status_code = 201
        return service.session_view(row, service.items(session, row), resumed=found == "resumed")
    return _run(operation)


@router.get("/sessions/{session_id}", response_model=SessionView)
def get_session_view(session_id: uuid.UUID, ctx: RequestContext = Depends(context_dep),
                     session: Session = Depends(get_session)):
    def operation():
        row = service.get(session, ctx.learner.id, session_id)
        return service.session_view(row, service.items(session, row))
    return _run(operation)


@router.post("/sessions/{session_id}/items/{item_id}/answer", response_model=AnswerResult)
def answer_item(session_id: uuid.UUID, item_id: uuid.UUID, body: AnswerBody,
                ctx: RequestContext = Depends(context_dep), session: Session = Depends(get_session)):
    return _run(lambda: service.respond(session, ctx.learner.id, session_id, item_id, request_id=body.request_id,
                                        answer=body.answer, hint_used=body.hint_used))


@router.post("/sessions/{session_id}/items/{item_id}/skip", response_model=AnswerResult)
def skip_item(session_id: uuid.UUID, item_id: uuid.UUID, body: SkipBody,
              ctx: RequestContext = Depends(context_dep), session: Session = Depends(get_session)):
    return _run(lambda: service.respond(session, ctx.learner.id, session_id, item_id, request_id=body.request_id,
                                        skip=body.reason))


@router.post("/sessions/{session_id}/finish", response_model=FinishResult)
def finish_session(session_id: uuid.UUID, body: FinishBody, ctx: RequestContext = Depends(context_dep),
                   session: Session = Depends(get_session)):
    return _run(lambda: service.finish(session, ctx.learner.id, session_id, request_id=body.request_id,
                                       early=body.early))
