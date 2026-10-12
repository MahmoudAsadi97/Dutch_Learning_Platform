"""Speech use cases: transcribe an upload, synthesise a reply. Usage is reserved before every provider call."""

from __future__ import annotations

import hashlib
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import func, select
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

        # A request id is for tracing, not permission to repeat a billable call for free.
        # Conversation retries are answered from persisted turns before reaching this function.
        call_id = uuid.uuid4().hex
        reservation = usage.reserve(
            session, settings, learner_id, "audio_seconds",
            max(1.0, canonical_info.duration_seconds), call_id,
        )
        usage.started(session, reservation.id)
        try:
            transcript = stt.transcribe(target, language="nl", request_id=request_id)
        except ProviderError:
            usage.release(session, reservation.id)
            raise
        usage.commit(session, reservation.id, canonical_info.duration_seconds)

        blob_key = f"recordings/{learner_id}/{call_id}.wav"
        stored = False
        storage_warning = None
        if keep_recording:
            try:
                blob.put(blob_key, target.read_bytes(), content_type="audio/wav")
                stored = True
            except ProviderError:
                # Transcription already succeeded. Preserve it and its usage even if storage fails.
                storage_warning = "recording_not_saved"

    asset = AudioAsset(
        learner_id=learner_id, kind="recording", blob_key=blob_key, container=settings.blob_container,
        source_container_format=source_info.container, source_codec=source_info.codec,
        source_bytes=len(upload_bytes), duration_seconds=canonical_info.duration_seconds,
        sample_rate=canonical_info.sample_rate, channels=canonical_info.channels,
        label="learner-recording", provider=stt.name, request_id=request_id,
        meta={"transcript": transcript.text, "stt_model": transcript.model, "stored": stored,
              "storage_warning": storage_warning},
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
    call_id = uuid.uuid4().hex
    reservation = usage.reserve(session, settings, learner_id, "audio_seconds", estimated_seconds, call_id)
    usage.started(session, reservation.id)
    try:
        result = tts.synthesize(text, request_id=request_id)
    except ProviderError:
        usage.release(session, reservation.id)
        raise
    seconds = _wav_seconds(result.wav_bytes, result.sample_rate)
    usage.commit(session, reservation.id, seconds)
    asset = None
    if store:
        blob_key = f"synthesis/{learner_id}/{call_id}.wav"
        stored = False
        try:
            blob.put(blob_key, result.wav_bytes, content_type="audio/wav")
            stored = True
        except ProviderError:
            pass  # The caller can still play the generated bytes; do not repeat the paid call.
        asset = AudioAsset(
            learner_id=learner_id, kind="synthesis", blob_key=blob_key, container=settings.blob_container,
            source_container_format="wav", source_codec="pcm_s16le", source_bytes=len(result.wav_bytes),
            duration_seconds=seconds, sample_rate=result.sample_rate, channels=1, label=result.label,
            provider=result.provider, request_id=request_id,
            meta={"voice": result.voice, "text": text, "stored": stored,
                  "storage_warning": None if stored else "audio_not_saved"},
        )
        session.add(asset)
        session.flush()
    return result.wav_bytes, asset, result.label


TTS_CACHE_PREFIX = "tts-cache"


def tts_cache_key(tts: TextToSpeech, text: str) -> str:
    digest = hashlib.sha256(" ".join(text.split()).encode()).hexdigest()
    return f"{TTS_CACHE_PREFIX}/{tts.name}/{tts.voice or 'default'}/{digest}.wav"


def synthesize_cached(
    session: Session,
    settings: Settings,
    *,
    learner_id: uuid.UUID,
    request_id: str,
    text: str,
    tts: TextToSpeech,
    blob: BlobStore,
) -> tuple[bytes, bool]:
    """Speech for a course text every learner shares (an exercise word or sentence), and whether it came from the
    cache. A hit costs no allowance; a miss is an ordinary paid synthesis, then kept under `tts-cache/` per
    provider and voice. The cache holds course text only, never a learner's own words, and sits under its own
    prefix, so removing a learner's recordings never touches it.

    A miss is made once: the first request for a text takes a transaction-scoped advisory lock on its cache key,
    so a simultaneous request for the same text waits, then finds the sound cached and pays nothing. A hit never
    waits for the lock."""
    text = " ".join(text.split())
    key = tts_cache_key(tts, text)
    cached = _cached(blob, key)
    if cached is None:
        session.execute(select(func.pg_advisory_xact_lock(func.hashtextextended(key, 0))))
        cached = _cached(blob, key)
    if cached is not None:
        return cached, True
    wav, _asset, _label = synthesize_text(session, settings, learner_id=learner_id, request_id=request_id, text=text,
                                          tts=tts, blob=blob)
    try:
        blob.put(key, wav, content_type="audio/wav")
    except ProviderError:
        pass  # the learner still hears it; the next request synthesises again
    return wav, False


def _cached(blob: BlobStore, key: str) -> bytes | None:
    try:
        return blob.get(key) if blob.exists(key) else None
    except ProviderError:
        return None  # an unreadable cache falls back to synthesis


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

