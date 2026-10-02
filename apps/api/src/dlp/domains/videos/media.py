"""Finishing a rendered file: pull the subtitle track out as cues, remux for progressive playback, measure."""
from __future__ import annotations

import logging
import re
from pathlib import Path

from dlp.domains.speech.audio import media_duration, run_tool

log = logging.getLogger(__name__)

_TIME = re.compile(r"(\d+):(\d\d):(\d\d)[,.](\d{1,3})")
_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)


def _seconds(stamp: str) -> float:
    match = _TIME.search(stamp)
    if not match:
        return 0.0
    hours, minutes, seconds, millis = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis.ljust(3, "0")) / 1000


def parse_srt(text: str) -> list[dict]:
    """SubRip blocks to cues: [{"start", "end", "text"}], tags stripped, blank cues dropped."""
    cues: list[dict] = []
    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n").strip()):
        lines = [line for line in block.split("\n") if line.strip()]
        if not lines:
            continue
        if "-->" not in lines[0] and len(lines) > 1 and "-->" in lines[1]:
            lines = lines[1:]
        if "-->" not in lines[0]:
            continue
        start_text, _, end_text = lines[0].partition("-->")
        body = " ".join(re.sub(r"<[^>]+>", "", line).strip() for line in lines[1:]).strip()
        if not body:
            continue
        start, end = _seconds(start_text), _seconds(end_text)
        if end <= start:
            end = start + 0.5
        cues.append({"start": round(start, 3), "end": round(end, 3), "text": body})
    return cues


def normalise(text: str) -> str:
    return " ".join(_WORD.findall(text.casefold()))


def assign_scenes(cues: list[dict], scenes: list[str]) -> list[dict]:
    """Attach the index of the scene each cue belongs to, by text containment, else by word overlap."""
    normal = [normalise(scene) for scene in scenes]
    last = 0
    out: list[dict] = []
    for cue in cues:
        needle = normalise(cue["text"])
        found = next((i for i, scene in enumerate(normal) if needle and needle in scene), None)
        if found is None:
            words = set(needle.split())
            scores = [(len(words & set(scene.split())), -abs(i - last), i) for i, scene in enumerate(normal)]
            best = max(scores, default=(0, 0, last))
            found = best[2] if best[0] > 0 else last
        last = found
        out.append({**cue, "scene": found})
    return out


def vtt_for(cues: list[dict]) -> str:
    def stamp(value: float) -> str:
        millis = int(round(value * 1000))
        hours, rest = divmod(millis, 3_600_000)
        minutes, rest = divmod(rest, 60_000)
        seconds, millis = divmod(rest, 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"
    lines = ["WEBVTT", ""]
    for index, cue in enumerate(cues, start=1):
        lines += [str(index), f"{stamp(cue['start'])} --> {stamp(cue['end'])}", cue["text"], ""]
    return "\n".join(lines)


def extract_cues(video: Path, *, timeout: float = 60.0, memory_limit_mb: int = 2048) -> list[dict]:
    """The first subtitle track as cues; an empty list when the file carries none."""
    completed = run_tool(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-i", str(video),
                          "-map", "0:s:0", "-f", "srt", "-"], timeout=timeout, memory_limit_mb=memory_limit_mb)
    if completed.returncode != 0:
        log.info("no subtitle track extracted: %s", completed.stderr.decode("utf-8", "replace").strip()[-160:])
        return []
    return parse_srt(completed.stdout.decode("utf-8", "replace"))


def remux(video: Path, target: Path, *, timeout: float = 120.0, memory_limit_mb: int = 2048) -> Path:
    """Video and audio only, index first (progressive playback); the source when remuxing fails."""
    completed = run_tool(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-i", str(video),
                          "-map", "0:v:0", "-map", "0:a:0?", "-c", "copy", "-movflags", "+faststart", str(target)],
                         timeout=timeout, memory_limit_mb=memory_limit_mb)
    if completed.returncode != 0 or not target.exists() or target.stat().st_size < 1024:
        log.warning("remux failed, keeping the rendered file: %s",
                    completed.stderr.decode("utf-8", "replace").strip()[-200:])
        return video
    return target


def finalize(raw: Path, folder: Path, scenes: list[str], *, timeout: float = 120.0,
             memory_limit_mb: int = 2048) -> tuple[Path, list[dict], float]:
    cues = assign_scenes(extract_cues(raw, timeout=timeout, memory_limit_mb=memory_limit_mb), scenes)
    final = remux(raw, folder / "final.mp4", timeout=timeout, memory_limit_mb=memory_limit_mb)
    duration = media_duration(final, timeout=timeout, memory_limit_mb=memory_limit_mb)
    if duration <= 0 and cues:
        duration = max(cue["end"] for cue in cues)
    return final, cues, round(duration, 3)
