"""Speech use cases: transcribe an upload, synthesise a reply. Usage is reserved before every provider call."""

from __future__ import annotations

import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from dlp.config import Settings
from dlp.domains.speech.audio import AudioError, AudioInfo, canonicalise
from dlp.domains.speech.models import AudioAsset
from dlp.domains.usage import service as usage
from dlp.providers.base import BlobStore, ProviderError, SpeechToText, TextToSpeech, Transcript


@dataclass
class TranscriptionOutcome:
    asset: AudioAsset
    source: AudioInfo
    canonical: AudioInfo
    transcript: Transcript


def transcribe_upload(
    session: Session,
    settings: Settings,
    *,
    learner_id: uuid.UUID,
    request_id: str,
    upload_bytes: bytes,
    upload_filename: str,
    stt: SpeechToText,
    blob: BlobStore,
    keep_recording: bool = True,
) -> TranscriptionOutcome:
    if len(upload_bytes) == 0:
        raise AudioError("empty upload")
    if len(upload_bytes) > settings.max_upload_bytes:
        raise AudioError(f"upload larger than {settings.max_upload_bytes} bytes", status_code=413)

    with tempfile.TemporaryDirectory(prefix="dlp-audio-") as tmp:
        tmp_dir = Path(tmp)
        source = tmp_dir / ("upload" + _safe_suffix(upload_filename))
        source.write_bytes(upload_bytes)
        target = tmp_dir / "canonical.wav"
        canonical_info = canonicalise(
            source, target, max_seconds=settings.max_audio_seconds,
            timeout=settings.ffmpeg_timeout_seconds, memory_limit_mb=settings.ffmpeg_memory_limit_mb,
        )
        source_info = _source_info(source, settings)

        reservation = usage.reserve(
            session, settings, learner_id, "audio_seconds",
            max(1.0, canonical_info.duration_seconds), request_id,
        )
        try:
            transcript = stt.transcribe(target, language="nl", request_id=request_id)
        except ProviderError:
            usage.release(session, reservation.id)
            raise
        usage.commit(session, reservation.id, canonical_info.duration_seconds)

        blob_key = f"recordings/{learner_id}/{request_id}.wav"
        if keep_recording:
            blob.put(blob_key, target.read_bytes(), content_type="audio/wav")

    asset = AudioAsset(
        learner_id=learner_id, kind="recording", blob_key=blob_key, container=settings.blob_container,
        source_container_format=source_info.container, source_codec=source_info.codec,
        source_bytes=len(upload_bytes), duration_seconds=canonical_info.duration_seconds,
        sample_rate=canonical_info.sample_rate, channels=canonical_info.channels,
        label="learner-recording", provider=stt.name, request_id=request_id,
        meta={"transcript": transcript.text, "stt_model": transcript.model, "stored": keep_recording},
    )
    session.add(asset)
    session.flush()
    return TranscriptionOutcome(asset=asset, source=source_info, canonical=canonical_info, transcript=transcript)


def synthesize_text(
    session: Session,
    settings: Settings,
    *,
    learner_id: uuid.UUID,
    request_id: str,
    text: str,
    tts: TextToSpeech,
    blob: BlobStore,
    store: bool = False,
) -> tuple[bytes, AudioAsset | None, str]:
    text = text.strip()
    if not text:
        raise AudioError("nothing to synthesise")
    if len(text) > 600:
        raise AudioError("text too long for one synthesis (600 characters)", status_code=413)
    estimated_seconds = max(1.0, len(text) / 14.0)
    reservation = usage.reserve(session, settings, learner_id, "audio_seconds", estimated_seconds, request_id)
    try:
        result = tts.synthesize(text, request_id=request_id)
    except ProviderError:
        usage.release(session, reservation.id)
        raise
    seconds = _wav_seconds(result.wav_bytes, result.sample_rate)
    usage.commit(session, reservation.id, seconds)
    asset = None
    if store:
        blob_key = f"synthesis/{learner_id}/{request_id}.wav"
        blob.put(blob_key, result.wav_bytes, content_type="audio/wav")
        asset = AudioAsset(
            learner_id=learner_id, kind="synthesis", blob_key=blob_key, container=settings.blob_container,
            source_container_format="wav", source_codec="pcm_s16le", source_bytes=len(result.wav_bytes),
            duration_seconds=seconds, sample_rate=result.sample_rate, channels=1, label=result.label,
            provider=result.provider, request_id=request_id, meta={"voice": result.voice, "text": text},
        )
        session.add(asset)
        session.flush()
    return result.wav_bytes, asset, result.label


def _safe_suffix(filename: str) -> str:
    suffix = Path(filename or "").suffix.lower()
    return suffix if suffix in {".webm", ".ogg", ".mp4", ".m4a", ".wav", ".mp3", ".flac", ".aac", ".mkv"} else ".bin"


def _source_info(source: Path, settings: Settings) -> AudioInfo:
    from dlp.domains.speech.audio import probe

    return probe(source, timeout=settings.ffmpeg_timeout_seconds, memory_limit_mb=settings.ffmpeg_memory_limit_mb)


def _wav_seconds(wav_bytes: bytes, sample_rate: int) -> float:
    import io
    import wave

    try:
        with wave.open(io.BytesIO(wav_bytes), "rb") as handle:
            return handle.getnframes() / float(handle.getframerate() or sample_rate or 16000)
    except wave.Error:
        return max(0.1, len(wav_bytes) / float(2 * (sample_rate or 16000)))
