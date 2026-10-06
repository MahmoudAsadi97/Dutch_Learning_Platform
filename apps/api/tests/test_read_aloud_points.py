"""D-23: read-aloud points reward the first attempt in which any word was recognised, whichever attempt that is."""

from __future__ import annotations

from dataclasses import replace

from dlp.api.deps import providers_dep
from dlp.providers.fixtures import FixtureSpeechToText
from dlp.providers.registry import get_providers

from .conftest import FIXTURES
from .test_stories import ready_episode


def test_read_aloud_points_are_granted_once_on_a_later_successful_attempt(client, headers):
    episode = ready_episode(client, headers)
    from dlp.main import app

    wav = (FIXTURES / "tone_1s.wav").read_bytes()

    def attempt(text: str) -> dict:
        app.dependency_overrides[providers_dep] = lambda: replace(get_providers(), stt=FixtureSpeechToText(default_text=text))
        try:
            response = client.post(f"/stories/episodes/{episode['id']}/read-aloud", headers=headers,
                                   data={"paragraph_index": "1"}, files={"audio": ("take.wav", wav, "audio/wav")})
        finally:
            app.dependency_overrides.pop(providers_dep, None)
        assert response.status_code == 200, response.text
        return response.json()

    silent = attempt("eh")
    assert silent["matched_words"] == 0 and silent["points"] == 0
    spoken = attempt("Sami gaat naar de bakkerij op de hoek.")
    assert spoken["matched_words"] > 0 and spoken["points"] == 5
    again = attempt("Sami gaat naar de bakkerij op de hoek.")
    assert again["points"] == 0
    stored = client.get(f"/stories/episodes/{episode['id']}", headers=headers).json()["read_aloud"]
    assert stored["1"]["attempts"] == 3 and stored["1"]["awarded"] is True
    assert client.get("/today", headers=headers).json()["goal"]["points"] >= 5
