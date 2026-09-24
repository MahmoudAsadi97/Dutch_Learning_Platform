"""Read-only suggestions are free; model ordering happens only after a deliberate POST."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from dlp.api.deps import RequestContext, context_dep, providers_dep, settings_dep
from dlp.api.routes_curriculum import _run
from dlp.config import Settings
from dlp.db.session import get_session
from dlp.domains.coaching import service
from dlp.domains.coaching.schemas import PlanBody
from dlp.providers.registry import Providers

router = APIRouter(prefix="/coach", tags=["practice"])


@router.get("/plan")
def plan_get(stage_id: str = Query(min_length=2, max_length=20), ctx: RequestContext = Depends(context_dep),
             session: Session = Depends(get_session)):
    return _run(lambda: service.get_plan(session, ctx.learner.id, stage_id))


@router.post("/plan")
def plan_post(body: PlanBody, ctx: RequestContext = Depends(context_dep), settings: Settings = Depends(settings_dep),
              providers: Providers = Depends(providers_dep), session: Session = Depends(get_session)):
    return _run(lambda: service.personalise_plan(session, settings, providers, learner_id=ctx.learner.id,
                                                 stage_id=body.stage_id, request_id=body.request_id))


@router.get("/history")
def history_get(stage_id: str = Query(min_length=2, max_length=20),
                limit: int = Query(default=20, ge=1, le=50), offset: int = Query(default=0, ge=0, le=100000),
                ctx: RequestContext = Depends(context_dep), session: Session = Depends(get_session)):
    return _run(lambda: service.history_page(session, ctx.learner.id, stage_id, limit, offset))
