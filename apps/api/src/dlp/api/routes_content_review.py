"""Editorial operations are available only to explicitly configured curriculum administrators."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from dlp.api.deps import RequestContext, context_dep, providers_dep, settings_dep
from dlp.api.routes_curriculum import _run
from dlp.config import Settings
from dlp.db.session import get_session
from dlp.domains.content_review import service
from dlp.domains.content_review.schemas import ReviewRequest
from dlp.domains.curriculum.service import is_admin
from dlp.providers.registry import Providers

router = APIRouter(prefix="/content-review", tags=["content review"])


def require_admin(ctx: RequestContext = Depends(context_dep), settings: Settings = Depends(settings_dep)):
    if not is_admin(settings, ctx.principal.email):
        raise HTTPException(status_code=403, detail="Content review is available to curriculum administrators only.")
    return ctx


@router.get("/{stage_id}")
def list_reviews(stage_id: str, offset: int = Query(default=0, ge=0, le=10000),
                 limit: int = Query(default=12, ge=1, le=24),
                 ctx: RequestContext = Depends(require_admin), providers: Providers = Depends(providers_dep),
                 session: Session = Depends(get_session)):
    return _run(lambda: service.list_topics(session, providers, stage_id, offset=offset, limit=limit))


@router.post("/{stage_id}")
def queue_reviews(stage_id: str, body: ReviewRequest, ctx: RequestContext = Depends(require_admin),
                  settings: Settings = Depends(settings_dep), providers: Providers = Depends(providers_dep),
                  session: Session = Depends(get_session)):
    return _run(lambda: service.queue_topics(session, settings, providers, requester_id=ctx.learner.id,
                                            stage_id=stage_id, topic_ids=body.topic_ids,
                                            retry_failed=body.retry_failed))
