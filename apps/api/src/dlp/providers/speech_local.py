"""Local speech providers: faster-whisper for recognition, Piper for synthesis.

Both run entirely on the laptop. Models are loaded lazily on first use and the
imports are deferred so that the API starts even when the optional
`speech-local` extra is not installed (preflight then reports them as missing).
"""

from __future__ import annotations

import io
import shutil
import subprocess
import sys
import threading
import time
import wave
from pathlib import Path
from typing import Any

from dlp.providers.base import (
    AudioResult,
    ProviderError,
    ProviderUnavailable,
    SpeechToText,
    TextToSpeech,
    Transcript,
    TranscriptSegment,
)


class FasterWhisperSpeechToText(SpeechToText):
    name = "local-faster-whisper"

    def __init__(self, model_size: str = "small", device: str = "cpu", compute_type: str = "int8",
                 cache_dir: Path | None = None) -> None:
        self.model = model_size
        self.device = device
        self.compute_type = compute_type
        self.cache_dir = cache_dir
        self._model: Any = None
        self._lock = threading.Lock()

    def available(self) -> tuple[bool, str]:
        try:
            import faster_whisper  # noqa: F401
        except ImportError:
            return False, "faster-whisper is not installed (pip install -e '.[speech-local]')"
        return True, f"faster-whisper model {self.model} on {self.device}/{self.compute_type}"

    def _load(self) -> Any:
        if self._model is None:
            with self._lock:
                if self._model is None:
                    try:
                        from faster_whisper import WhisperModel
                    except ImportError as exc:
                        raise ProviderUnavailable("faster-whisper is not installed") from exc
                    kwargs: dict[str, Any] = {"device": self.device, "compute_type": self.compute_type}
                    if self.cache_dir is not None:
                        self.cache_dir.mkdir(parents=True, exist_ok=True)
                        kwargs["download_root"] = str(self.cache_dir)
                    self._model = WhisperModel(self.model, **kwargs)
        return self._model

    def transcribe(self, wav_path: Path, *, language: str = "nl", request_id: str = "") -> Transcript:
        model = self._load()
        started = time.monotonic()
        try:
            segments_iter, info = model.transcribe(str(wav_path), language=language, beam_size=5, vad_filter=True)
            segments = [TranscriptSegment(start=float(s.start), end=float(s.end), text=s.text.strip())
                        for s in segments_iter]
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"faster-whisper failed: {exc}") from exc
        text = " ".join(segment.text for segment in segments).strip()
        return Transcript(
            text=text, language=str(getattr(info, "language", language)),
            duration_seconds=float(getattr(info, "duration", 0.0)), provider=self.name, model=self.model,
            segments=segments, confidence=getattr(info, "language_probability", None),
            latency_ms=int((time.monotonic() - started) * 1000),
        )


class PiperTextToSpeech(TextToSpeech):
    """Synthesises with a Piper voice (`nl_BE-*` preferred, `nl_NL-*` otherwise); always labelled synthetic."""

    name = "local-piper"
    label = "synthetic-development"

    def __init__(self, voice: str, voices_dir: Path, timeout_seconds: float = 60.0) -> None:
        self.voice = voice
        self.voices_dir = voices_dir
        self.timeout_seconds = timeout_seconds

    @property
    def model_path(self) -> Path:
        return self.voices_dir / f"{self.voice}.onnx"

    def available(self) -> tuple[bool, str]:
        if not self.model_path.exists() or not self.model_path.with_suffix(".onnx.json").exists():
            return False, f"voice files missing: {self.model_path} (run scripts/fetch_piper_voice.py)"
        try:
            import piper  # noqa: F401
        except ImportError:
            if shutil.which("piper") is None:
                return False, "piper-tts is not installed (pip install -e '.[speech-local]')"
        return True, f"piper voice {self.voice}"

    def synthesize(self, text: str, *, request_id: str = "") -> AudioResult:
        ok, detail = self.available()
        if not ok:
            raise ProviderUnavailable(detail)
        started = time.monotonic()
        wav_bytes = self._synthesize_python(text)
        if wav_bytes is None:
            wav_bytes = self._synthesize_cli(text)
        sample_rate = _wav_sample_rate(wav_bytes)
        return AudioResult(
            wav_bytes=wav_bytes, sample_rate=sample_rate, voice=self.voice, provider=self.name,
            label=self.label, latency_ms=int((time.monotonic() - started) * 1000),
        )

    def _synthesize_python(self, text: str) -> bytes | None:
        try:
            from piper import PiperVoice
        except ImportError:
            return None
        voice = PiperVoice.load(str(self.model_path))
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as handle:
            if hasattr(voice, "synthesize_wav"):
                voice.synthesize_wav(text, handle)
            else:  # piper-tts < 1.3
                voice.synthesize(text, handle)
        return buffer.getvalue()

    def _synthesize_cli(self, text: str) -> bytes:
        executable = shutil.which("piper")
        command = [executable] if executable else [sys.executable, "-m", "piper"]
        command += ["--model", str(self.model_path), "--output-raw"]
        try:
            completed = subprocess.run(
                command, input=text.encode("utf-8"), capture_output=True, timeout=self.timeout_seconds, check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ProviderError("piper timed out") from exc
        if completed.returncode != 0:
            raise ProviderError(f"piper failed: {completed.stderr.decode('utf-8', 'replace')[:300]}")
        sample_rate = _voice_sample_rate(self.model_path.with_suffix(".onnx.json"))
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(sample_rate)
            handle.writeframes(completed.stdout)
        return buffer.getvalue()


def _wav_sample_rate(wav_bytes: bytes) -> int:
    with wave.open(io.BytesIO(wav_bytes), "rb") as handle:
        return handle.getframerate()


def _voice_sample_rate(config_path: Path) -> int:
    import json

    try:
        return int(json.loads(config_path.read_text(encoding="utf-8"))["audio"]["sample_rate"])
    except (OSError, KeyError, ValueError):
        return 22050
