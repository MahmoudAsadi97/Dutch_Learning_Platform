"""Authenticated topic-first practice. Transient marks never become progress."""
from __future__ import annotations

import io
import wave

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile
from sqlalchemy.orm import Session

from dlp.api.deps import RequestContext, context_dep, db_session, providers_dep, settings_dep
from dlp.api.routes_curriculum import _run
from dlp.config import Settings
from dlp.domains.curriculum.schemas import Skill
from dlp.domains.curriculum.service import CurriculumError, audio_parts
from dlp.domains.speech.service import synthesize_cached, transcribe_upload
from dlp.domains.study import content, feedback
from dlp.domains.study.responses import StudyCatalogue, StudyFeedback, StudyLesson, StudyTranscription
from dlp.domains.study.schemas import FeedbackBody
from dlp.providers.base import ProviderError
from dlp.providers.registry import Providers

router = APIRouter(prefix="/study/{stage_id}/topics", tags=["study"])


@router.get("", response_model=StudyCatalogue)
def topic_catalogue(stage_id: str, skill: Skill, q: str = Query(default="", max_length=120),
                    topic_group: str = Query(default="", max_length=100),
                    ctx: RequestContext = Depends(context_dep)):
    return content.catalogue(stage_id, skill, query=q, topic_group=topic_group)


@router.get("/{topic_id}", response_model=StudyLesson)
def topic_lesson(stage_id: str, topic_id: str, skill: Skill,
                 activity_id: str | None = Query(default=None, max_length=100),
                 ctx: RequestContext = Depends(context_dep), settings: Settings = Depends(settings_dep)):
    result = content.lesson(stage_id, topic_id, skill, activity_id=activity_id)
    result["policy"]["recording_max_seconds"] = min(60, settings.max_audio_seconds)
    return result


@router.post("/{topic_id}/feedback", response_model=StudyFeedback)
def topic_feedback(stage_id: str, topic_id: str, body: FeedbackBody,
                   ctx: RequestContext = Depends(context_dep), settings: Settings = Depends(settings_dep),
                   providers: Providers = Depends(providers_dep), session: Session = db_session):
    return _run(lambda: feedback.evaluate(
        session, settings, providers.chat_strong, learner_id=ctx.learner.id, stage_id=stage_id,
        topic_id=topic_id, body=body, request_id=ctx.request_id), provider_detail=(
            "Practice feedback is temporarily unavailable. No score was saved; your response is still on this page."))


@router.post("/{topic_id}/audio", response_class=Response, responses={200: {"content": {"audio/wav": {"schema": {
    "type": "string", "format": "binary"}}}, "description": "A continuous synthetic Dutch practice recording."}})
def topic_audio(stage_id: str, topic_id: str, part: str = Query(min_length=1, max_length=80),
                skill: Skill = "listening", activity_id: str | None = Query(default=None, max_length=100),
                ctx: RequestContext = Depends(context_dep), settings: Settings = Depends(settings_dep),
                providers: Providers = Depends(providers_dep), session: Session = db_session):
    def operation():
        lesson = content.lesson(stage_id, topic_id, skill, activity_id=activity_id)
        selected = next((item for item in lesson["parts"] if item["id"] == part), None)
        if selected is None or not selected["text"]:
            raise CurriculumError("this study part has no authored recording", 404)
        text = " ".join(line["nl"] for line in selected["text"])
        if len(text) > 12000:
            raise CurriculumError("this recording is too long for a single practice request", 422)
        recordings = []
        all_cached = True
        for chunk in audio_parts(text):
            wav, cached = synthesize_cached(session, settings, learner_id=ctx.learner.id,
                                           request_id=ctx.request_id, text=chunk,
                                           tts=providers.tts, blob=providers.blob)
            recordings.append(wav)
            all_cached = all_cached and cached
        # One coherent script becomes one playback resource. Joining verified
        # PCM frames avoids sentence-by-sentence browser playback gaps.
        frames = []
        parameters = None
        try:
            for recording in recordings:
                with wave.open(io.BytesIO(recording), "rb") as wav:
                    current = (wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getcomptype())
                    if parameters is not None and current != parameters:
                        raise ProviderError("recording chunks used incompatible audio formats")
                    parameters = current
                    frames.append(wav.readframes(wav.getnframes()))
            if parameters is None:
                raise ProviderError("recording had no audio")
            output = io.BytesIO()
            with wave.open(output, "wb") as wav:
                wav.setnchannels(parameters[0])
                wav.setsampwidth(parameters[1])
                wav.setframerate(parameters[2])
                wav.writeframes(b"".join(frames))
        except (wave.Error, EOFError) as exc:
            raise ProviderError("recording could not be assembled") from exc
        return Response(output.getvalue(), media_type="audio/wav", headers={
            "Cache-Control": "no-store", "X-Audio-Label": providers.tts.label,
            "X-Audio-Voice": providers.tts.voice, "X-Audio-Cached": "1" if all_cached else "0"})
    return _run(operation)


@router.post("/{topic_id}/transcribe", response_model=StudyTranscription)
def topic_transcribe(stage_id: str, topic_id: str, audio: UploadFile = File(...),
                     ctx: RequestContext = Depends(context_dep), settings: Settings = Depends(settings_dep),
                     providers: Providers = Depends(providers_dep), session: Session = db_session):
    def operation():
        content.require_stage(stage_id)
        document, _ = content.documents()
        if not any(topic.id == topic_id for topic in document.topics):
            raise CurriculumError("study topic not found", 404)
        outcome = transcribe_upload(
            session, settings, learner_id=ctx.learner.id, request_id=ctx.request_id,
            upload_bytes=audio.file.read(settings.max_upload_bytes + 1), upload_filename=audio.filename or "recording",
            stt=providers.stt, blob=providers.blob, keep_recording=False, persist_asset=False)
        return {"transcript": {"text": outcome.transcript.text, "language": outcome.transcript.language,
                               "segments": [segment.__dict__ for segment in outcome.transcript.segments]},
                "audio": {"stored": False, "asset_id": None}, "ephemeral": True}
    return _run(operation, provider_detail="Transcription is temporarily unavailable. No recording was saved.")
