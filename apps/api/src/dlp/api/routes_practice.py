from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from dlp.api.deps import RequestContext, context_dep
from dlp.db.session import get_session
from dlp.domains.content.service import get_mission
from dlp.domains.practice.models import PracticeSession
from dlp.domains.practice.service import PracticeError, get_session_for_learner, list_sessions, start_session
from dlp.domains.progress.service import ensure_skill_records

router = APIRouter(prefix="/practice", tags=["practice"])


class StartSessionRequest(BaseModel):
    mission_id: str = Field(pattern=r"^[a-z0-9-]+$")
    variant: str = Field(default="base", pattern=r"^(base|transfer)$")


def _session_view(practice: PracticeSession) -> dict:
    return {
        "id": str(practice.id),
        "mission_id": practice.mission_id,
        "variant": practice.variant,
        "status": practice.status,
        "current_step_key": practice.current_step_key,
        "request_id": practice.request_id,
        "state": practice.state,
        "started_at": practice.started_at.isoformat(),
        "updated_at": practice.updated_at.isoformat(),
        "completed_at": practice.completed_at.isoformat() if practice.completed_at else None,
        "turn_count": len(practice.turns),
        "evidence_count": len(practice.evidence),
    }


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
    return {"session": _session_view(practice), "request_id": ctx.request_id}


@router.get("/sessions")
def index(ctx: RequestContext = Depends(context_dep), session: Session = Depends(get_session)) -> dict:
    return {"sessions": [_session_view(p) for p in list_sessions(session, ctx.learner.id)], "request_id": ctx.request_id}


@router.get("/sessions/{session_id}")
def show(session_id: uuid.UUID, ctx: RequestContext = Depends(context_dep),
         session: Session = Depends(get_session)) -> dict:
    try:
        practice = get_session_for_learner(session, ctx.learner.id, session_id)
    except PracticeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.reason) from exc
    return {
        "session": _session_view(practice),
        "turns": [
            {"id": str(t.id), "turn_index": t.turn_index, "step_key": t.step_key, "modality": t.modality,
             "learner_text": t.learner_text, "character_text": t.character_text, "status": t.status,
             "action_result": t.action_result, "created_at": t.created_at.isoformat()}
            for t in practice.turns
        ],
        "evidence": [
            {"id": str(e.id), "step_key": e.step_key, "skill": e.skill, "kind": e.kind, "modality": e.modality,
             "payload": e.payload, "source": e.source, "created_at": e.created_at.isoformat()}
            for e in practice.evidence
        ],
        "request_id": ctx.request_id,
    }
