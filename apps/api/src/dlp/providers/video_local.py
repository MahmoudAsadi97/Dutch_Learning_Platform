"""Scene-card renderer: the configured voice reads each scene over a drawn card with its key word.

This is the laptop renderer (Piper voice) and the cheap renderer anywhere (any voice): it needs only
ffmpeg. Each scene becomes one segment (a flat card with the key word and the title, the narration as
audio, a short pause), the segments are joined, and the Dutch subtitles are embedded as a text track with
one cue per sentence timed from the audio. Rendering is synchronous; the finished file waits in the work
directory until the job fetches it.
"""
from __future__ import annotations

import io
import logging
import re
import shutil
import uuid
import wave
from pathlib import Path

from dlp.domains.speech.audio import run_tool, tools_available
from dlp.providers.base import ProviderError, TextToSpeech, VideoJobStatus, VideoRenderer, VideoRequest

log = logging.getLogger(__name__)

SCENE_PAUSE_SECONDS = 0.6
_SENTENCE_END = re.compile(r"(?<=[.!?…])\s+(?=[^\s])")
PALETTE = ["0x1F3A5F", "0x2F5D50", "0x6B3F2A", "0x4A3F6B", "0x7A5C1E", "0x3B5A7A", "0x5C2E4A"]


def split_sentences(text: str) -> list[str]:
    parts = [p.strip() for p in _SENTENCE_END.split(text.strip()) if p.strip()]
    return parts or [text.strip()]


def wav_seconds(wav_bytes: bytes) -> float:
    with wave.open(io.BytesIO(wav_bytes), "rb") as handle:
        return handle.getnframes() / float(handle.getframerate() or 16000)


def _timestamp(seconds: float) -> str:
    millis = int(round(seconds * 1000))
    hours, rest = divmod(millis, 3_600_000)
    minutes, rest = divmod(rest, 60_000)
    secs, millis = divmod(rest, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def srt_for(scenes: list[tuple[str, float, float]]) -> str:
    """One cue per sentence; a scene's time is shared between its sentences by length."""
    lines: list[str] = []
    index = 1
    for text, start, duration in scenes:
        sentences = split_sentences(text)
        total = sum(len(s) for s in sentences) or 1
        cursor = start
        for sentence in sentences:
            share = duration * len(sentence) / total
            lines += [str(index), f"{_timestamp(cursor)} --> {_timestamp(cursor + share)}", sentence, ""]
            cursor += share
            index += 1
    return "\n".join(lines) + "\n"


class SceneCardRenderer(VideoRenderer):
    label = "scene-cards"

    def __init__(self, tts: TextToSpeech, *, work_dir: Path, name: str = "scene-cards", width: int = 960,
                 height: int = 540, font: str = "", fast: bool = False, timeout_seconds: float = 180.0,
                 memory_limit_mb: int = 2048) -> None:
        self.tts = tts
        self.name = name
        self.voice = tts.voice
        self.work_dir = work_dir
        self.width, self.height = (480, 270) if fast else (width, height)
        self.font = font
        self.fast = fast
        self.timeout_seconds = timeout_seconds
        self.memory_limit_mb = memory_limit_mb

    def available(self) -> tuple[bool, str]:
        if not tools_available():
            return False, "ffmpeg/ffprobe are not installed"
        return True, f"scene cards with voice {self.voice or self.tts.name}"

    def _job_dir(self, job_id: str) -> Path:
        if not re.fullmatch(r"[a-z0-9-]{8,80}", job_id):
            raise ProviderError("invalid render job id")
        return self.work_dir / "render" / job_id

    # --- rendering --------------------------------------------------------------------------------------

    def start(self, request: VideoRequest, *, request_id: str = "") -> str:
        if not request.scenes:
            raise ProviderError("nothing to render")
        if not tools_available():
            raise ProviderError("ffmpeg/ffprobe are not installed")
        job_id = f"cards-{uuid.uuid4().hex}"
        folder = self._job_dir(job_id)
        folder.mkdir(parents=True, exist_ok=True)
        try:
            self._render(request, folder, request_id)
        except Exception:
            shutil.rmtree(folder, ignore_errors=True)
            raise
        return job_id

    def _render(self, request: VideoRequest, folder: Path, request_id: str) -> None:
        timeline: list[tuple[str, float, float]] = []
        segments: list[Path] = []
        cursor = 0.0
        for index, scene in enumerate(request.scenes):
            audio = self.tts.synthesize(scene.text, request_id=f"{request_id}-{index}" if request_id else "")
            wav_path = folder / f"scene-{index}.wav"
            wav_path.write_bytes(audio.wav_bytes)
            seconds = max(wav_seconds(audio.wav_bytes), 0.2)
            segment = folder / f"segment-{index}.mp4"
            self._segment(segment, wav_path, seconds + SCENE_PAUSE_SECONDS, index, scene.keyword, request.title)
            timeline.append((scene.text, cursor, seconds))
            cursor += seconds + SCENE_PAUSE_SECONDS
            segments.append(segment)
        (folder / "subtitles.srt").write_text(srt_for(timeline), encoding="utf-8")
        listing = folder / "segments.txt"
        listing.write_text("".join(f"file '{segment.name}'\n" for segment in segments), encoding="utf-8")
        output = folder / "out.mp4"
        command = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                   "-f", "concat", "-safe", "0", "-i", str(listing), "-i", str(folder / "subtitles.srt"),
                   "-map", "0:v:0", "-map", "0:a:0", "-map", "1:s:0", "-c:v", "copy", "-c:a", "copy",
                   "-c:s", "mov_text", "-metadata:s:s:0", "language=nld", "-movflags", "+faststart", str(output)]
        completed = run_tool(command, timeout=self.timeout_seconds, memory_limit_mb=self.memory_limit_mb)
        if completed.returncode != 0 or not output.exists():
            log.warning("ffmpeg concat failed: %s", completed.stderr.decode("utf-8", "replace")[-400:])
            raise ProviderError("video assembly failed")

    def _segment(self, target: Path, wav_path: Path, seconds: float, index: int, keyword: str, title: str) -> None:
        colour = PALETTE[index % len(PALETTE)]
        base = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", f"color=c={colour}:s={self.width}x{self.height}:r=25:d={seconds:.3f}",
                "-i", str(wav_path)]
        encode = ["-c:v", "libx264", "-preset", "ultrafast" if self.fast else "veryfast", "-pix_fmt", "yuv420p",
                  "-c:a", "aac", "-b:a", "96k", "-af", "apad", "-shortest", "-t", f"{seconds:.3f}", str(target)]
        texts = self._text_filters(target.parent, index, keyword, title)
        if texts:
            completed = run_tool([*base, "-vf", texts, *encode], timeout=self.timeout_seconds,
                                 memory_limit_mb=self.memory_limit_mb)
            if completed.returncode == 0 and target.exists():
                return
            log.info("drawtext unavailable (%s); rendering plain cards",
                     completed.stderr.decode("utf-8", "replace").strip()[-160:] or "no output")
        completed = run_tool([*base, *encode], timeout=self.timeout_seconds, memory_limit_mb=self.memory_limit_mb)
        if completed.returncode != 0 or not target.exists():
            log.warning("ffmpeg segment failed: %s", completed.stderr.decode("utf-8", "replace")[-400:])
            raise ProviderError("video rendering failed")

    def _text_filters(self, folder: Path, index: int, keyword: str, title: str) -> str:
        if self.fast:
            return ""
        keyword_file = folder / f"keyword-{index}.txt"
        keyword_file.write_text(keyword.strip()[:40] or " ", encoding="utf-8")
        title_file = folder / "title.txt"
        title_file.write_text(title.strip()[:60] or " ", encoding="utf-8")
        font = f"fontfile='{self.font}':" if self.font else ""
        big = max(28, self.height // 8)
        small = max(16, self.height // 22)
        return (f"drawtext={font}textfile='{keyword_file}':fontcolor=white:fontsize={big}:x=(w-text_w)/2:y=(h-text_h)/2,"
                f"drawtext={font}textfile='{title_file}':fontcolor=white@0.75:fontsize={small}:x=(w-text_w)/2:y=h-{small * 3}")

    # --- job lifecycle ----------------------------------------------------------------------------------

    def status(self, job_id: str) -> VideoJobStatus:
        output = self._job_dir(job_id) / "out.mp4"
        if output.exists():
            return VideoJobStatus("succeeded")
        return VideoJobStatus("failed", detail="no rendered file for this job")

    def fetch(self, job_id: str, destination: Path) -> None:
        output = self._job_dir(job_id) / "out.mp4"
        if not output.exists():
            raise ProviderError("rendered file is gone")
        shutil.copyfile(output, destination)

    def cleanup(self, job_id: str) -> None:
        try:
            shutil.rmtree(self._job_dir(job_id), ignore_errors=True)
        except ProviderError:
            pass
