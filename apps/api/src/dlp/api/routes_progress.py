from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from dlp.api.deps import RequestContext, context_dep, settings_dep
from dlp.config import Settings
from dlp.db.base import utcnow
from dlp.db.session import get_session
from dlp.domains.curriculum.models import CurriculumAttempt, CurriculumPractice
from dlp.domains.feedback.service import report_view, reports_for
from dlp.domains.practice.service import list_sessions
from dlp.domains.practice.turns import evidence_view, turn_view
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


@router.get("/export")
def export(ctx: RequestContext = Depends(context_dep), settings: Settings = Depends(settings_dep),
           session: Session = Depends(get_session)) -> JSONResponse:
    """Owner-only JSON export of everything stored about the learner: records, sessions, turns, evidence, feedback."""
    if ctx.principal.email.lower() not in {e.lower() for e in settings.allowlist}:
        raise HTTPException(status_code=403, detail="export is limited to the owner allowlist")
    sessions = list_sessions(session, ctx.learner.id)
    payload = {
        "exported_at": utcnow().isoformat(),
        "learner": {"id": str(ctx.learner.id), "email": ctx.learner.email, "display_name": ctx.learner.display_name,
                    "support_language": ctx.learner.support_language, "target_language": ctx.learner.target_language},
        "skill_records": [
            {"id": str(r.id), "mission_id": r.mission_id, "skill": r.skill, "status": r.status, "attempts": r.attempts,
             "latest_assessment": r.latest_assessment, "evidence_ids": r.evidence_ids, "updated_at": r.updated_at.isoformat()}
            for r in skill_records_for(session, ctx.learner.id)
        ],
        "sessions": [
            {
                "id": str(p.id), "mission_id": p.mission_id, "variant": p.variant, "status": p.status,
                "current_step_key": p.current_step_key, "state": p.state, "started_at": p.started_at.isoformat(),
                "updated_at": p.updated_at.isoformat(), "completed_at": p.completed_at.isoformat() if p.completed_at else None,
                "turns": [turn_view(t) for t in p.turns],
                "evidence": [evidence_view(e) for e in p.evidence],
                "feedback": [report_view(r) for r in reports_for(session, p)],
            }
            for p in sessions
        ],
        "curriculum": {
            "practice": [
                {"stage_id": p.stage_id, "skill": p.skill, "completed": p.completed,
                 "evidence": p.evidence, "updated_at": p.updated_at.isoformat()}
                for p in session.scalars(select(CurriculumPractice).where(CurriculumPractice.learner_id == ctx.learner.id))
            ],
            "checks": [
                {"id": str(a.id), "stage_id": a.stage_id, "status": a.status, "admin_preview": a.admin_preview,
                 "submission": a.submission, "results": a.results, "created_at": a.created_at.isoformat(),
                 "completed_at": a.completed_at.isoformat() if a.completed_at else None}
                for a in session.scalars(select(CurriculumAttempt).where(CurriculumAttempt.learner_id == ctx.learner.id))
            ],
        },
        "usage": snapshot(session, settings, ctx.learner.id),
        "request_id": ctx.request_id,
    }
    stamp = utcnow().strftime("%Y%m%d-%H%M%S")
    return JSONResponse(content=payload, headers={
        "Content-Disposition": f'attachment; filename="learner-export-{stamp}.json"',
        "X-Request-Id": ctx.request_id, "Cache-Control": "no-store",
    })
