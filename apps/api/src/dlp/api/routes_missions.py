from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from dlp.api.deps import RequestContext, context_dep
from dlp.db.session import get_session
from dlp.domains.content.acceptance import check_a01
from dlp.domains.content.schemas import UNREVIEWED_LABEL_FA, UNREVIEWED_LABEL_NL, review_summary
from dlp.domains.content.service import get_mission, list_missions, mission_document
from dlp.domains.progress.service import ensure_skill_records

router = APIRouter(prefix="/missions", tags=["missions"])


def _summary(mission) -> dict:
    document = mission_document(mission)
    summary = review_summary(document)
    return {
        "id": mission.id,
        "version": mission.version,
        "cefr_target": mission.cefr_target,
        "title": document.title.model_dump(),
        "description": document.description.model_dump(),
        "review_status": mission.review_status,
        "content_hash": mission.content_hash,
        "fixed_word_count": mission.fixed_word_count,
        "word_limit": document.content_pack.word_limit,
        "review": summary.model_dump(),
        "steps": [
            {"key": step.key, "skill": step.skill, "type": step.payload.type, "variant": step.variant,
             "title": step.title.model_dump()}
            for step in document.steps
        ],
    }


@router.get("")
def missions(ctx: RequestContext = Depends(context_dep), session: Session = Depends(get_session)) -> dict:
    return {"missions": [_summary(m) for m in list_missions(session)], "request_id": ctx.request_id}


@router.get("/{mission_id}")
def mission(mission_id: str, ctx: RequestContext = Depends(context_dep), session: Session = Depends(get_session)) -> dict:
    record = get_mission(session, mission_id)
    if record is None:
        raise HTTPException(status_code=404, detail="mission not found")
    ensure_skill_records(session, ctx.learner.id, record.id)
    document = mission_document(record)
    return {
        **_summary(record),
        "document": document.model_dump(mode="json"),
        "labels": {"unreviewed_nl": UNREVIEWED_LABEL_NL, "unreviewed_fa": UNREVIEWED_LABEL_FA},
        "request_id": ctx.request_id,
    }


@router.get("/{mission_id}/steps/{step_key}")
def step(mission_id: str, step_key: str, ctx: RequestContext = Depends(context_dep),
         session: Session = Depends(get_session)) -> dict:
    record = get_mission(session, mission_id)
    if record is None:
        raise HTTPException(status_code=404, detail="mission not found")
    document = mission_document(record)
    found = next((s for s in document.steps if s.key == step_key), None)
    if found is None:
        raise HTTPException(status_code=404, detail="step not found")
    return {"mission_id": mission_id, "step": found.model_dump(mode="json"),
            "labels": {"unreviewed_nl": UNREVIEWED_LABEL_NL, "unreviewed_fa": UNREVIEWED_LABEL_FA},
            "request_id": ctx.request_id}


@router.get("/{mission_id}/acceptance/A01")
def acceptance_a01(mission_id: str, ctx: RequestContext = Depends(context_dep),
                   session: Session = Depends(get_session)) -> dict:
    return {**check_a01(session, mission_id).as_dict(), "request_id": ctx.request_id}
