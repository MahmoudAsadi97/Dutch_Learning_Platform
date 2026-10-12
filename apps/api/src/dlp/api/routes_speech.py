from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from dlp.api.deps import RequestContext, context_dep, db_session, providers_dep, settings_dep
from dlp.config import Settings
from dlp.domains.activity.service import reached, record_activity
from dlp.domains.speech.compare import read_aloud_compare, require_words
from dlp.domains.speech.service import synthesize_text, transcribe_upload
from dlp.providers.base import ProviderError, ProviderUnavailable
from dlp.providers.registry import Providers

router = APIRouter(prefix="/speech", tags=["speech"])


@router.post("/transcribe")
def transcribe(
    audio: UploadFile = File(...),
    keep_recording: bool = Form(default=True),
    purpose: Literal["warmup"] | None = Form(default=None),
    ctx: RequestContext = Depends(context_dep),
    settings: Settings = Depends(settings_dep),
    providers: Providers = Depends(providers_dep),
    session: Session = db_session,
) -> dict:
    """Run blocking audio, database and provider work in FastAPI's worker pool."""
    data = audio.file.read(settings.max_upload_bytes + 1)
    try:
        outcome = transcribe_upload(
            session, settings, learner_id=ctx.learner.id, request_id=ctx.request_id, upload_bytes=data,
            upload_filename=audio.filename or "", stt=providers.stt, blob=providers.blob, keep_recording=keep_recording,
        )
    except ProviderUnavailable as exc:
        raise HTTPException(status_code=503, detail=f"speech-to-text unavailable: {exc}") from exc
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=f"speech-to-text failed: {exc}") from exc
    goal: dict[str, bool] = {}
    if purpose == "warmup" and outcome.transcript.text.strip():
        # the microphone warm-up with recognised speech: 2 points once a day (D-34); other recordings earn theirs
        # where they are used
        goal = reached(record_activity(session, ctx.learner.id, kind="speech_warmup", ref="speech-warmup",
                                       request_id=ctx.request_id))
    return {
        **goal,
        "request_id": ctx.request_id,
        "transcript": {
            "text": outcome.transcript.text,
            "language": outcome.transcript.language,
            "segments": [s.__dict__ for s in outcome.transcript.segments],
            "provider": outcome.transcript.provider,
            "model": outcome.transcript.model,
            "latency_ms": outcome.transcript.latency_ms,
        },
        "audio": {
            "asset_id": str(outcome.asset.id),
            "blob_key": outcome.asset.blob_key if outcome.asset.meta.get("stored") else None,
            "stored": bool(outcome.asset.meta.get("stored")),
            "storage_warning": outcome.asset.meta.get("storage_warning"),
            "source": outcome.source.__dict__,
            "canonical": outcome.canonical.__dict__,
        },
        "evidence": {"modality": "speech", "kind": "transcript"},
    }


class ReadAloudResult(BaseModel):
    """Recognised words only: there is deliberately no score (D-20)."""

    transcript: str
    target_words: int
    matched_words: int
    missed: list[str]
    extra: list[str]


@router.post("/read-aloud", response_model=ReadAloudResult)
def read_aloud(
    text: str = Form(min_length=1, max_length=600),
    audio: UploadFile = File(...),
    ctx: RequestContext = Depends(context_dep),
    settings: Settings = Depends(settings_dep),
    providers: Providers = Depends(providers_dep),
    session: Session = db_session,
) -> ReadAloudResult:
    """Read any text aloud and see which words were recognised. The recording is not kept and nothing is
    awarded or scored; the audio seconds count against the allowance like any transcription. A speech
    service that fails answers 503 with its code through the shared handler."""
    require_words(text)
    outcome = transcribe_upload(
        session, settings, learner_id=ctx.learner.id, request_id=ctx.request_id,
        upload_bytes=audio.file.read(settings.max_upload_bytes + 1), upload_filename=audio.filename or "recording",
        stt=providers.stt, blob=providers.blob, keep_recording=False,
    )
    return ReadAloudResult(transcript=outcome.transcript.text, **read_aloud_compare(text, outcome.transcript.text))


class SynthesisRequest(BaseModel):
    text: str = Field(min_length=1, max_length=600)
    store: bool = False


@router.post("/synthesize")
def synthesize(
    body: SynthesisRequest,
    ctx: RequestContext = Depends(context_dep),
    settings: Settings = Depends(settings_dep),
    providers: Providers = Depends(providers_dep),
    session: Session = db_session,
) -> Response:
    try:
        wav_bytes, asset, label = synthesize_text(
            session, settings, learner_id=ctx.learner.id, request_id=ctx.request_id, text=body.text,
            tts=providers.tts, blob=providers.blob, store=body.store,
        )
    except ProviderUnavailable as exc:
        raise HTTPException(status_code=503, detail=f"text-to-speech unavailable: {exc}") from exc
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=f"text-to-speech failed: {exc}") from exc
    headers = {
        "X-Audio-Label": label,
        "X-Audio-Voice": providers.tts.voice,
        "X-Request-Id": ctx.request_id,
        "Cache-Control": "no-store",
    }
    if asset is not None:
        if asset.meta.get("stored"):
            headers["X-Audio-Asset-Id"] = str(asset.id)
        else:
            headers["X-Audio-Storage-Warning"] = "audio_not_saved"
    return Response(content=wav_bytes, media_type="audio/wav", headers=headers)
