"""Inspect uploaded audio and canonicalise it to mono 16 kHz signed 16-bit PCM WAV.

Every subprocess call uses an argument list (no shell), a timeout, a memory
limit where the platform supports it, and the input size and duration are
bounded before ffmpeg runs.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)

ALLOWED_CONTAINERS = {"matroska", "webm", "ogg", "mov", "mp4", "m4a", "3gp", "wav", "flac", "mp3", "aac", "mpeg"}
ALLOWED_CODECS = {"opus", "vorbis", "aac", "pcm_s16le", "pcm_f32le", "flac", "mp3", "pcm_u8", "pcm_s24le", "pcm_s32le"}
CANONICAL_SAMPLE_RATE = 16000


class AudioError(Exception):
    def __init__(self, reason: str, *, status_code: int = 400) -> None:
        super().__init__(reason)
        self.reason = reason
        self.status_code = status_code


@dataclass(frozen=True)
class AudioInfo:
    container: str
    codec: str
    duration_seconds: float
    sample_rate: int
    channels: int
    size_bytes: int


def tools_available() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def _limit_memory(limit_mb: int):
    """Return a preexec function that caps the child's *virtual address space* (POSIX only; 0 disables).

    The cap must leave room for every shared library ffmpeg maps and for its thread stacks: full-featured
    builds (conda-forge, distribution packages with many codecs) need well over 1 GB of address space even
    though they use little real memory. A cap that is too small shows up as "failed to map segment".
    """
    if sys.platform.startswith("win") or limit_mb <= 0:
        return None
    import resource

    def apply() -> None:
        limit = limit_mb * 1024 * 1024
        try:
            resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
        except (ValueError, OSError):
            pass

    return apply


def _run(command: list[str], *, timeout: float, memory_limit_mb: int) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            command, capture_output=True, timeout=timeout, check=False, stdin=subprocess.DEVNULL,
            preexec_fn=_limit_memory(memory_limit_mb),
        )
    except subprocess.TimeoutExpired as exc:
        raise AudioError("audio processing timed out", status_code=422) from exc
    except OSError as exc:
        raise AudioError(f"cannot start {command[0]}", status_code=500) from exc


def probe(path: Path, *, timeout: float = 20.0, memory_limit_mb: int = 2048) -> AudioInfo:
    if not tools_available():
        raise AudioError("ffmpeg/ffprobe are not installed", status_code=500)
    command = [
        "ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", "-select_streams", "a:0",
        str(path),
    ]
    completed = _run(command, timeout=timeout, memory_limit_mb=memory_limit_mb)
    if completed.returncode != 0:
        _log_tool_failure("ffprobe", completed, memory_limit_mb)
        raise AudioError("the upload is not a readable audio file")
    try:
        data = json.loads(completed.stdout.decode("utf-8", "replace"))
    except json.JSONDecodeError as exc:
        raise AudioError("ffprobe output could not be parsed") from exc
    streams = data.get("streams") or []
    if not streams:
        raise AudioError("the upload contains no audio stream")
    stream = streams[0]
    fmt = data.get("format") or {}
    container = str(fmt.get("format_name", "")).split(",")[0].lower()
    codec = str(stream.get("codec_name", "")).lower()
    duration = float(stream.get("duration") or fmt.get("duration") or 0.0)
    return AudioInfo(
        container=container, codec=codec, duration_seconds=duration,
        sample_rate=int(stream.get("sample_rate") or 0), channels=int(stream.get("channels") or 0),
        size_bytes=path.stat().st_size,
    )


def canonicalise(source: Path, target: Path, *, max_seconds: float, timeout: float = 20.0,
                 memory_limit_mb: int = 2048) -> AudioInfo:
    """Validate `source` and write the canonical WAV to `target`. Returns the canonical file's info."""
    info = probe(source, timeout=timeout, memory_limit_mb=memory_limit_mb)
    if info.container not in ALLOWED_CONTAINERS:
        raise AudioError(f"unsupported audio container: {info.container or 'unknown'}")
    if info.codec not in ALLOWED_CODECS:
        raise AudioError(f"unsupported audio codec: {info.codec or 'unknown'}")
    if info.duration_seconds > max_seconds + 0.5:
        raise AudioError(f"recording is longer than {max_seconds:.0f} seconds", status_code=413)
    command = [
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-threads", "1",
        "-t", f"{max_seconds:.2f}",
        "-i", str(source),
        "-vn", "-ac", "1", "-ar", str(CANONICAL_SAMPLE_RATE), "-acodec", "pcm_s16le", "-f", "wav",
        str(target),
    ]
    completed = _run(command, timeout=timeout, memory_limit_mb=memory_limit_mb)
    if completed.returncode != 0 or not target.exists() or target.stat().st_size < 100:
        _log_tool_failure("ffmpeg", completed, memory_limit_mb)
        raise AudioError("audio conversion failed", status_code=422)
    canonical = probe(target, timeout=timeout, memory_limit_mb=memory_limit_mb)
    if canonical.duration_seconds <= 0.05:
        raise AudioError("recording is empty")
    return canonical


def _log_tool_failure(tool: str, completed: subprocess.CompletedProcess[bytes], memory_limit_mb: int) -> None:
    """Keep the diagnosis server-side: the client only learns that conversion failed."""
    stderr = completed.stderr.decode("utf-8", "replace").strip()
    hint = ""
    if "failed to map segment" in stderr or "cannot allocate memory" in stderr.lower():
        hint = f" (address-space cap FFMPEG_MEMORY_LIMIT_MB={memory_limit_mb} is too small for this {tool} build)"
    log.warning("%s exited with %s%s: %s", tool, completed.returncode, hint, stderr[-400:] or "(no stderr)")
