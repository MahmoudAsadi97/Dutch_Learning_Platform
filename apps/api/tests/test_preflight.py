"""Preflight reports the Azure adapters from stored evidence of real work, never from a paid call."""
from __future__ import annotations

from dlp.db.session import session_scope
from dlp.domains.identity.models import Learner
from dlp.domains.speech.models import AudioAsset
from dlp.domains.stories import service
from dlp.domains.stories.models import StoryEpisode
from dlp.providers.preflight import run_preflight


def _azure_settings(settings):
    return settings.model_copy(update={
        "chat_provider": "azure", "azure_chat_endpoint": "https://example.openai.azure.com",
        "azure_chat_deployment_small": "chat-small", "azure_chat_deployment_strong": "chat-strong",
        "stt_provider": "azure", "tts_provider": "azure", "azure_speech_region": "westeurope",
        "azure_speech_key": "k" * 32, "max_audio_seconds": 60,
    })


def _items(settings) -> dict[str, tuple[str, str]]:
    return {item.component: (item.status, item.detail) for item in run_preflight(settings, check_network=False)}


def test_azure_components_are_pending_until_a_stored_record_proves_live_use(database, settings):
    azure = _azure_settings(settings)
    before = _items(azure)
    for component in ("chat model", "speech to text", "text to speech"):
        status, detail = before[component]
        assert status == "integration_pending" and detail.endswith("no live use recorded yet"), (component, detail)
        assert "not tested" not in detail

    with session_scope() as session:
        learner = Learner(subject="fixture:preflight@example.com", email="preflight@example.com")
        session.add(learner)
        session.flush()
        series = service.ensure_series(session, learner)
        session.add(StoryEpisode(learner_id=learner.id, series_id=series.id, number=1, stage_id="a1", status="ready",
                                 provider="azure-strong", model="gpt-4.1-mini-2025-04-14"))
        session.add(AudioAsset(learner_id=learner.id, kind="synthesis", blob_key="preflight/reply.wav",
                               container="learner-audio", provider="azure-speech"))

    after = _items(azure)
    assert after["chat model"][0] == "ok" and "last live use 20" in after["chat model"][1]
    assert after["text to speech"][0] == "ok" and "last live use 20" in after["text to speech"][1]
    assert after["speech to text"][0] == "integration_pending", "no Azure recording was stored"
    assert after["chat model"][1].startswith("endpoint and deployments configured")


def test_a_failed_or_local_episode_is_not_evidence_for_the_azure_model(database, settings):
    with session_scope() as session:
        learner = Learner(subject="fixture:preflight2@example.com", email="preflight2@example.com")
        session.add(learner)
        session.flush()
        series = service.ensure_series(session, learner)
        session.add(StoryEpisode(learner_id=learner.id, series_id=series.id, number=1, stage_id="a1", status="failed",
                                 provider="azure-strong"))
        session.add(StoryEpisode(learner_id=learner.id, series_id=series.id, number=2, stage_id="a1", status="ready",
                                 provider="local-ollama", model="llama3.1:8b"))
    assert _items(_azure_settings(settings))["chat model"][0] == "integration_pending"
