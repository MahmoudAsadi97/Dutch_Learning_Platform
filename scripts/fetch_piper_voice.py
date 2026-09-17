#!/usr/bin/env python3
"""Download a Piper voice for local synthesis (Phase A).

    python scripts/fetch_piper_voice.py                 # voice from LOCAL_TTS_VOICE in .env (default nl_BE-nathalie-medium)
    python scripts/fetch_piper_voice.py nl_NL-mls-medium

Preference order for release 0.1: an `nl_BE` voice if one exists in the Piper voice
list, otherwise an `nl_NL` voice. Files land in LOCAL_TTS_VOICES_DIR (default
`.local/piper-voices`, ignored by Git). The audio is development audio and is always
labelled synthetic in the app; the fixed audio is regenerated with Azure voices in Phase B.
"""

from __future__ import annotations

import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0"
KNOWN_NL_VOICES = {
    # name: (language dir, speaker, quality) — from the Piper voice list at the time of writing
    "nl_BE-nathalie-medium": ("nl/nl_BE", "nathalie", "medium"),
    "nl_BE-nathalie-x_low": ("nl/nl_BE", "nathalie", "x_low"),
    "nl_BE-rdh-medium": ("nl/nl_BE", "rdh", "medium"),
    "nl_BE-rdh-x_low": ("nl/nl_BE", "rdh", "x_low"),
    "nl_NL-mls-medium": ("nl/nl_NL", "mls", "medium"),
    "nl_NL-mls_5809-low": ("nl/nl_NL", "mls_5809", "low"),
    "nl_NL-mls_7432-low": ("nl/nl_NL", "mls_7432", "low"),
    "nl_NL-pim-medium": ("nl/nl_NL", "pim", "medium"),
    "nl_NL-ronnie-medium": ("nl/nl_NL", "ronnie", "medium"),
}


def read_env(name: str, default: str) -> str:
    value = os.environ.get(name)
    if value:
        return value
    dotenv = ROOT / ".env"
    if dotenv.exists():
        for line in dotenv.read_text(encoding="utf-8").splitlines():
            if line.startswith(f"{name}="):
                return line.split("=", 1)[1].split(" #", 1)[0].strip()
    return default


def download(url: str, target: Path) -> None:
    print(f"downloading {url}")
    with urllib.request.urlopen(url, timeout=120) as response, target.open("wb") as handle:  # noqa: S310
        while chunk := response.read(1 << 20):
            handle.write(chunk)
    print(f"  -> {target} ({target.stat().st_size // 1024} KiB)")


def main() -> int:
    voice = sys.argv[1] if len(sys.argv) > 1 else read_env("LOCAL_TTS_VOICE", "nl_BE-nathalie-medium")
    voices_dir = Path(read_env("LOCAL_TTS_VOICES_DIR", "./.local/piper-voices"))
    if not voices_dir.is_absolute():
        voices_dir = ROOT / voices_dir
    voices_dir.mkdir(parents=True, exist_ok=True)
    if voice not in KNOWN_NL_VOICES:
        print(f"unknown voice {voice}; known Dutch voices: {', '.join(KNOWN_NL_VOICES)}", file=sys.stderr)
        print("check the current list at https://huggingface.co/rhasspy/piper-voices", file=sys.stderr)
        return 2
    language_dir, speaker, quality = KNOWN_NL_VOICES[voice]
    for suffix in (".onnx", ".onnx.json"):
        target = voices_dir / f"{voice}{suffix}"
        if target.exists() and target.stat().st_size > 0:
            print(f"already present: {target}")
            continue
        download(f"{BASE}/{language_dir}/{speaker}/{quality}/{voice}{suffix}", target)
    print(f"done; set LOCAL_TTS_VOICE={voice} in .env if it differs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
