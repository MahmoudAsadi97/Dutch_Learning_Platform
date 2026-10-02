"""Video lessons. Reads are free; a deliberate POST queues a model call and a render against the counters."""
from __future__ import annotations

import re
import uuid
from collections.abc import Callable, Iterator

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

from dlp.api.deps import RequestContext, context_dep, providers_dep, settings_dep
from dlp.config import Settings
from dlp.db.session import get_session
from dlp.domains.curriculum.service import CurriculumError
from dlp.domains.stories import vocab
from dlp.domains.usage.service import UsageLimitExceeded
from dlp.domains.videos import service
from dlp.domains.videos.schemas import RequestVideoBody, VideoAnswerBody, VideoRateBody, VideoWordBody
from dlp.providers.base import ProviderError
from dlp.providers.registry import Providers

router = APIRouter(prefix="/videos", tags=["videos"])

CHUNK = 512 * 1024
RANGE = re.compile(r"^bytes=(\d*)-(\d*)$")


def _run(operation: Callable):
    try:
        return operation()
    except (CurriculumError, vocab.VocabError) as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except UsageLimitExceeded:
        return JSONResponse(status_code=429, content={"detail": "Your practice allowance is used up. Try again later."})
    except ProviderError:
        return JSONResponse(status_code=503, content={"detail": "The language service is temporarily unavailable. "
                                                                 "Your progress is saved; try again in a moment."})


def _uuid(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="not found") from exc


@router.get("")
def list_videos(ctx: RequestContext = Depends(context_dep), settings: Settings = Depends(settings_dep),
                providers: Providers = Depends(providers_dep), session: Session = Depends(get_session)):
    return _run(lambda: service.library(session, ctx.learner, settings, providers))


@router.post("", status_code=201)
def request_video(body: RequestVideoBody, ctx: RequestContext = Depends(context_dep),
                  session: Session = Depends(get_session)):
    return _run(lambda: service.video_view(service.request_video(
        session, ctx.learner, stage_id=body.stage_id, topic=body.topic, kind=body.kind, request_id=body.request_id),
        full=False))


@router.get("/{video_id}")
def get_video(video_id: str, ctx: RequestContext = Depends(context_dep), session: Session = Depends(get_session)):
    return _run(lambda: service.video_view(service.get_video(session, ctx.learner, _uuid(video_id))))


@router.get("/{video_id}/subtitles.vtt")
def subtitles(video_id: str, ctx: RequestContext = Depends(context_dep), session: Session = Depends(get_session)):
    text = _run(lambda: service.subtitles(service.get_video(session, ctx.learner, _uuid(video_id))))
    if not isinstance(text, str):
        return text
    return Response(content=text, media_type="text/vtt; charset=utf-8",
                    headers={"Cache-Control": "private, max-age=3600"})


@router.get("/{video_id}/media")
def media(video_id: str, range_header: str | None = Header(default=None, alias="Range"),
          ctx: RequestContext = Depends(context_dep), providers: Providers = Depends(providers_dep),
          session: Session = Depends(get_session)):
    """The MP4 with byte ranges, so the player can seek without downloading everything."""
    located = _run(lambda: service.media_for(service.get_video(session, ctx.learner, _uuid(video_id))))
    if not isinstance(located, tuple):
        return located
    key, size = located
    if size <= 0:
        size = _run(lambda: providers.blob.size(key))
        if not isinstance(size, int):
            return size
    start, end = 0, size - 1
    status = 200
    if range_header:
        match = RANGE.match(range_header.strip())
        if not match:
            return Response(status_code=416, headers={"Content-Range": f"bytes */{size}"})
        first, last = match.groups()
        if first:
            start = int(first)
            end = min(int(last), size - 1) if last else size - 1
        elif last:
            start = max(size - int(last), 0)
        if start >= size or start > end:
            return Response(status_code=416, headers={"Content-Range": f"bytes */{size}"})
        status = 206
    length = end - start + 1

    def body() -> Iterator[bytes]:
        offset = start
        remaining = length
        while remaining > 0:
            piece = providers.blob.get_range(key, offset, min(CHUNK, remaining))
            if not piece:
                break
            yield piece
            offset += len(piece)
            remaining -= len(piece)

    headers = {"Accept-Ranges": "bytes", "Content-Length": str(length), "Cache-Control": "private, max-age=3600",
               "Content-Disposition": "inline"}
    if status == 206:
        headers["Content-Range"] = f"bytes {start}-{end}/{size}"
    return StreamingResponse(body(), status_code=status, media_type="video/mp4", headers=headers)


@router.post("/{video_id}/watched")
def watched(video_id: str, ctx: RequestContext = Depends(context_dep), session: Session = Depends(get_session)):
    return _run(lambda: service.mark_watched(
        session, ctx.learner, service.get_video(session, ctx.learner, _uuid(video_id), lock=True)))


@router.post("/{video_id}/answers")
def answers(video_id: str, body: VideoAnswerBody, ctx: RequestContext = Depends(context_dep),
            session: Session = Depends(get_session)):
    return _run(lambda: service.answer_questions(
        session, ctx.learner, service.get_video(session, ctx.learner, _uuid(video_id), lock=True),
        request_id=body.request_id, answers=body.answers))


@router.post("/{video_id}/rating")
def rating(video_id: str, body: VideoRateBody, ctx: RequestContext = Depends(context_dep),
           session: Session = Depends(get_session)):
    return _run(lambda: service.rate(
        session, ctx.learner, service.get_video(session, ctx.learner, _uuid(video_id), lock=True), body.rating))


@router.post("/{video_id}/words")
def save_word(video_id: str, body: VideoWordBody, ctx: RequestContext = Depends(context_dep),
              session: Session = Depends(get_session)):
    return _run(lambda: service.save_word(
        session, ctx.learner, service.get_video(session, ctx.learner, _uuid(video_id)), body.term))


@router.post("/{video_id}/retry")
def retry(video_id: str, ctx: RequestContext = Depends(context_dep), session: Session = Depends(get_session)):
    return _run(lambda: service.retry_failed(
        session, ctx.learner, service.get_video(session, ctx.learner, _uuid(video_id), lock=True)))
