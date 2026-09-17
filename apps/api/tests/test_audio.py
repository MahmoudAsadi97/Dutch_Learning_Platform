import shutil
import subprocess
from pathlib import Path

import pytest

from dlp.domains.speech.audio import AudioError, canonicalise, probe
from dlp.providers.fixtures import tone_wav

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
                                reason="ffmpeg/ffprobe not installed")


def make_webm_opus(path: Path, seconds: float = 1.5, sample_rate: int = 48000) -> None:
    """Produce what a browser's MediaRecorder typically uploads: WebM container, Opus codec, 48 kHz stereo."""
    subprocess.run(
        ["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
         f"sine=frequency=440:sample_rate={sample_rate}:duration={seconds}",
         "-ac", "2", "-c:a", "libopus", "-b:a", "48k", str(path)],
        check=True, capture_output=True,
    )


def test_probe_reports_container_and_codec(tmp_path):
    source = tmp_path / "in.webm"
    make_webm_opus(source)
    info = probe(source)
    assert info.container in {"matroska", "webm"}
    assert info.codec == "opus"
    assert info.channels == 2
    assert 1.3 <= info.duration_seconds <= 1.7


def test_canonicalise_produces_mono_16k_pcm(tmp_path):
    source = tmp_path / "in.webm"
    make_webm_opus(source)
    target = tmp_path / "out.wav"
    info = canonicalise(source, target, max_seconds=30)
    assert info.container == "wav"
    assert info.codec == "pcm_s16le"
    assert info.sample_rate == 16000
    assert info.channels == 1
    assert 1.3 <= info.duration_seconds <= 1.7


def test_wav_input_is_accepted_too(tmp_path):
    source = tmp_path / "in.wav"
    source.write_bytes(tone_wav(0.8))
    info = canonicalise(source, tmp_path / "out.wav", max_seconds=30)
    assert info.codec == "pcm_s16le" and info.sample_rate == 16000


def test_too_long_recordings_are_refused(tmp_path):
    source = tmp_path / "long.webm"
    make_webm_opus(source, seconds=4.0)
    with pytest.raises(AudioError) as excinfo:
        canonicalise(source, tmp_path / "out.wav", max_seconds=2)
    assert excinfo.value.status_code == 413


def test_non_audio_uploads_are_refused(tmp_path):
    source = tmp_path / "notes.webm"
    source.write_bytes(b"this is not audio at all" * 100)
    with pytest.raises(AudioError, match="not a readable audio file"):
        canonicalise(source, tmp_path / "out.wav", max_seconds=30)


def test_timeout_is_enforced(tmp_path, monkeypatch):
    source = tmp_path / "in.webm"
    make_webm_opus(source)
    import dlp.domains.speech.audio as audio

    def slow_run(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs.get("timeout", 0))

    monkeypatch.setattr(audio.subprocess, "run", slow_run)
    with pytest.raises(AudioError, match="timed out") as excinfo:
        probe(source, timeout=0.001)
    assert excinfo.value.status_code == 422
