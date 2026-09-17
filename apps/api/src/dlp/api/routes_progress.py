from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from dlp.api.deps import RequestContext, context_dep, settings_dep
from dlp.config import Settings
from dlp.db.session import get_session
from dlp.domains.progress.service import skill_records_for
from dlp.domains.usage.service import snapshot

router = APIRouter(tags=["progress"])


@router.get("/progress")
def progress(ctx: RequestContext = Depends(context_dep), session: Session = Depends(get_session)) -> dict:
    return {
        "learner": {"id": str(ctx.learner.id), "email": ctx.learner.email, "display_name": ctx.learner.display_name,
                    "support_language": ctx.learner.support_language, "target_language": ctx.learner.target_language},
        "skill_records": [
            {"id": str(r.id), "mission_id": r.mission_id, "skill": r.skill, "status": r.status, "attempts": r.attempts,
             "latest_assessment": r.latest_assessment, "evidence_ids": r.evidence_ids, "updated_at": r.updated_at.isoformat()}
            for r in skill_records_for(session, ctx.learner.id)
        ],
        "request_id": ctx.request_id,
    }


@router.get("/usage")
def usage(ctx: RequestContext = Depends(context_dep), settings: Settings = Depends(settings_dep),
          session: Session = Depends(get_session)) -> dict:
    return {**snapshot(session, settings, ctx.learner.id), "request_id": ctx.request_id}
