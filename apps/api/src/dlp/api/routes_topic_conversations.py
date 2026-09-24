"""Learner-owned, bounded practice conversations. Browsing and help incur no model calls."""
from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field, StrictInt
from sqlalchemy.orm import Session

from dlp.api.deps import RequestContext, context_dep, providers_dep, settings_dep
from dlp.api.routes_curriculum import _run
from dlp.config import Settings
from dlp.db.session import get_session
from dlp.domains.topic_conversations import service
from dlp.domains.topic_conversations.content import blueprint_for
from dlp.providers.registry import Providers

router = APIRouter(prefix="/topic-conversations", tags=["curriculum"])


class StartBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    blueprint_id: str = Field(min_length=1, max_length=80, pattern=r"^[a-z0-9-]+$")
    request_id: str = Field(min_length=8, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")
    mode: Literal["typed", "spoken"]


class TurnBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    client_turn_id: str = Field(min_length=8, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")
    expected_turn: StrictInt = Field(ge=0, le=6)
    action: Literal["respond", "repeat", "hint"] = "respond"
    text: str = Field(default="", max_length=2000)
    audio_asset_id: uuid.UUID | None = None


@router.get("")
def conversations(stage_id: str | None = Query(default=None, max_length=20),
                  ctx: RequestContext = Depends(context_dep), session: Session = Depends(get_session)):
    return _run(lambda: service.listing(session, ctx.learner.id, stage_id))


@router.get("/blueprints/{blueprint_id}")
def blueprint(blueprint_id: str, ctx: RequestContext = Depends(context_dep), settings: Settings = Depends(settings_dep)):
    return _run(lambda: service.blueprint_view(blueprint_for(blueprint_id), settings))


@router.post("/start")
def start(body: StartBody, ctx: RequestContext = Depends(context_dep), settings: Settings = Depends(settings_dep),
          session: Session = Depends(get_session)):
    return _run(lambda: service.view(service.start(session, ctx.learner.id, **body.model_dump()), settings))


@router.get("/{conversation_id}")
def get(conversation_id: uuid.UUID, ctx: RequestContext = Depends(context_dep), settings: Settings = Depends(settings_dep),
        session: Session = Depends(get_session)):
    return _run(lambda: service.view(service.get(session, ctx.learner.id, conversation_id), settings))


@router.post("/{conversation_id}/turns")
def turn(conversation_id: uuid.UUID, body: TurnBody, ctx: RequestContext = Depends(context_dep),
         settings: Settings = Depends(settings_dep), providers: Providers = Depends(providers_dep),
         session: Session = Depends(get_session)):
    def operation():
        row = service.get(session, ctx.learner.id, conversation_id, lock=True)
        return service.view(service.turn(session, settings, providers, row, **body.model_dump(),
                                         request_id=ctx.request_id), settings)
    return _run(operation, provider_detail="Conversation feedback is temporarily unavailable. "
                "Your response was not added; keep it and retry.")


@router.post("/{conversation_id}/end")
def end(conversation_id: uuid.UUID, ctx: RequestContext = Depends(context_dep), settings: Settings = Depends(settings_dep),
        session: Session = Depends(get_session)):
    return _run(lambda: service.view(service.finish(session, service.get(session, ctx.learner.id, conversation_id,
                                                                         lock=True)), settings))
