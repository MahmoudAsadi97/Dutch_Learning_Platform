"""Authenticated, paginated content; no changes to learner scores or test evidence."""
from fastapi import APIRouter, Depends, HTTPException, Query

from dlp.api.deps import RequestContext, context_dep
from dlp.domains.curriculum import library
from dlp.domains.curriculum.service import CurriculumError

router = APIRouter(prefix="/library", tags=["library"])


def _bank(stage_id: str):
    try:
        return library.library_for(stage_id)
    except CurriculumError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.get("/{stage_id}")
def overview(stage_id: str, ctx: RequestContext = Depends(context_dep)):
    return {**library.summary(_bank(stage_id)), "learner_key": str(ctx.learner.id)}


@router.get("/{stage_id}/vocabulary")
def words(stage_id: str, q: str = Query(default="", max_length=120), topic: str = Query(default="", max_length=160),
          offset: int = Query(default=0, ge=0, le=100000), limit: int = Query(default=20, ge=1, le=50),
          ctx: RequestContext = Depends(context_dep)):
    return library.vocabulary_page(_bank(stage_id), query=q, topic=topic, offset=offset, limit=limit)


@router.get("/{stage_id}/stories")
def stories(stage_id: str, q: str = Query(default="", max_length=120), topic: str = Query(default="", max_length=160),
            offset: int = Query(default=0, ge=0, le=100000), limit: int = Query(default=12, ge=1, le=30),
            ctx: RequestContext = Depends(context_dep)):
    return library.story_page(_bank(stage_id), query=q, topic=topic, offset=offset, limit=limit)


@router.get("/{stage_id}/stories/{story_id}")
def story(stage_id: str, story_id: str, ctx: RequestContext = Depends(context_dep)):
    try:
        return library.story_detail(_bank(stage_id), story_id)
    except CurriculumError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
