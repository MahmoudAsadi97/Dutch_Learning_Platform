from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from dlp.api.deps import RequestContext, context_dep, providers_dep, settings_dep
from dlp.config import Settings
from dlp.db.session import get_session
from dlp.domains.content.acceptance import check_a01
from dlp.domains.content.schemas import UNREVIEWED_LABEL_FA, UNREVIEWED_LABEL_NL, ListeningPayload, review_summary
from dlp.domains.content.service import get_mission, list_missions, mission_document
from dlp.domains.practice.acceptance import CHECKS as PRACTICE_CHECKS
from dlp.domains.progress.service import ensure_skill_records
from dlp.domains.speech.audio import AudioError
from dlp.domains.speech.service import synthesize_text
from dlp.domains.usage.service import UsageLimitExceeded
from dlp.providers.base import ProviderError, ProviderUnavailable
from dlp.providers.registry import Providers

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


@router.get("/{mission_id}/acceptance/{check_id}")
def acceptance(mission_id: str, check_id: str, ctx: RequestContext = Depends(context_dep),
               session: Session = Depends(get_session)) -> dict:
    """One acceptance check (A01–A06) or `all`; read-only, so it may be run at any time."""
    checks = {"A01": check_a01, **PRACTICE_CHECKS}
    if check_id.lower() == "all":
        reports = [check(session, mission_id) for check in checks.values()]
        return {"passed": all(r.passed for r in reports), "checks": [r.as_dict() for r in reports],
                "request_id": ctx.request_id}
    check = checks.get(check_id.upper())
    if check is None:
        raise HTTPException(status_code=404, detail=f"unknown check; available: all, {', '.join(checks)}")
    return {**check(session, mission_id).as_dict(), "request_id": ctx.request_id}


@router.get("/{mission_id}/audio/{audio_key:path}")
def fixed_audio(
    mission_id: str,
    audio_key: str,
    ctx: RequestContext = Depends(context_dep),
    settings: Settings = Depends(settings_dep),
    providers: Providers = Depends(providers_dep),
    session: Session = Depends(get_session),
) -> Response:
    """The fixed audio of a listening step. In Phase A it is synthesised once from the transcript with the local
    voice, stored in the blob store under the step's `audio_key` and served with its label; Phase B replaces the
    stored file with the Azure `nl-BE` voice (OWNER_ACTIONS)."""
    record = get_mission(session, mission_id)
    if record is None:
        raise HTTPException(status_code=404, detail="mission not found")
    document = mission_document(record)
    step = next((s for s in document.steps if isinstance(s.payload, ListeningPayload) and s.payload.audio_key == audio_key), None)
    if step is None:
        raise HTTPException(status_code=404, detail="no listening step uses this audio key")
    label = "synthetic-development"
    voice = ""
    if providers.blob.exists(audio_key):
        wav_bytes = providers.blob.get(audio_key)
        try:
            meta = json.loads(providers.blob.get(audio_key + ".json"))
            label, voice = str(meta.get("label", label)), str(meta.get("voice", ""))
        except ProviderError:
            pass
    else:
        try:
            wav_bytes, _asset, label = synthesize_text(
                session, settings, learner_id=ctx.learner.id, request_id=ctx.request_id,
                text=step.payload.transcript.nl, tts=providers.tts, blob=providers.blob, store=False,  # type: ignore[union-attr]
            )
        except UsageLimitExceeded as exc:
            raise HTTPException(status_code=429, detail=str(exc)) from exc
        except ProviderUnavailable as exc:
            raise HTTPException(status_code=503, detail=f"text-to-speech unavailable: {exc}") from exc
        except (ProviderError, AudioError) as exc:
            raise HTTPException(status_code=502, detail=f"text-to-speech failed: {exc}") from exc
        voice = providers.tts.voice
        providers.blob.put(audio_key, wav_bytes, content_type="audio/wav")
        providers.blob.put(audio_key + ".json", json.dumps({"label": label, "voice": voice, "text": step.payload.transcript.nl,  # type: ignore[union-attr]
                                                            "request_id": ctx.request_id}).encode("utf-8"),
                           content_type="application/json")
    headers = {"X-Audio-Label": label, "X-Audio-Voice": voice, "X-Request-Id": ctx.request_id,
               "Cache-Control": "private, max-age=86400"}
    return Response(content=wav_bytes, media_type="audio/wav", headers=headers)
