"""Builds the configured providers. This is the only place that decides local vs Azure vs fixture."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dlp.config import Settings, get_settings
from dlp.providers.base import BlobStore, ChatModel, ProviderUnavailable, SpeechToText, TextToSpeech, VideoRenderer
from dlp.providers.blob_azure import AzureBlobStore
from dlp.providers.chat_openai_compatible import ChatEndpoint, OpenAICompatibleChatModel
from dlp.providers.fixtures import FixtureChatModel, FixtureSpeechToText, FixtureTextToSpeech, MemoryBlobStore
from dlp.providers.speech_azure import AzureSpeechToText, AzureTextToSpeech
from dlp.providers.speech_local import FasterWhisperSpeechToText, PiperTextToSpeech
from dlp.providers.video_azure import AzureAvatarRenderer, endpoint_for
from dlp.providers.video_local import SceneCardRenderer


@dataclass
class Providers:
    chat: ChatModel
    chat_strong: ChatModel
    stt: SpeechToText
    tts: TextToSpeech
    blob: BlobStore
    video: VideoRenderer

    def describe(self) -> dict[str, dict]:
        return {
            "chat": self.chat.describe(),
            "chat_strong": self.chat_strong.describe(),
            "stt": self.stt.describe(),
            "tts": self.tts.describe(),
            "blob": self.blob.describe(),
            "video": self.video.describe(),
        }


def _chat_token_provider(scope: str):
    """Lazy SDK construction: configured is not the same as a verified cloud connection."""
    provider = None

    def token() -> str:
        nonlocal provider
        try:
            if provider is None:
                from azure.identity import DefaultAzureCredential, get_bearer_token_provider
                provider = get_bearer_token_provider(DefaultAzureCredential(), scope)
            return provider()
        except Exception as exc:
            raise ProviderUnavailable("Azure chat identity could not obtain an access token") from exc
    return token


def build_chat(settings: Settings, tier: str = "small") -> ChatModel:
    if settings.chat_provider == "fixture":
        return FixtureChatModel()
    if settings.chat_provider == "azure":
        deployment = (settings.azure_chat_deployment_strong or settings.azure_chat_deployment_small
                      if tier == "strong" else settings.azure_chat_deployment_small)
        endpoint = ChatEndpoint(
            kind="azure_openai", base_url=settings.azure_chat_endpoint, model=deployment or "",
            api_key=settings.azure_chat_api_key, api_version=settings.azure_chat_api_version,
            timeout_seconds=settings.chat_timeout_seconds,
            token_provider=None if settings.azure_chat_api_key else _chat_token_provider(settings.azure_chat_token_scope),
        )
        return OpenAICompatibleChatModel(endpoint, name=f"azure-{tier}", max_attempts=settings.chat_max_attempts,
                                         max_concurrent=settings.max_concurrent_model_calls)
    model = settings.local_chat_model
    if tier == "strong" and settings.local_chat_model_strong:
        model = settings.local_chat_model_strong
    endpoint = ChatEndpoint(kind="ollama", base_url=settings.local_chat_base_url, model=model,
                            timeout_seconds=settings.chat_timeout_seconds)
    return OpenAICompatibleChatModel(endpoint, name=f"local-ollama-{tier}", max_attempts=settings.chat_max_attempts,
                                     max_concurrent=settings.max_concurrent_model_calls)


def _speech_token_provider(settings: Settings):
    """Managed identity (or developer login) tokens when no key is configured; None otherwise."""
    if settings.azure_speech_key or not settings.azure_speech_resource_id:
        return None
    from dlp.providers.speech_azure import managed_identity_token_provider

    try:
        return managed_identity_token_provider()
    except Exception:  # noqa: BLE001 - reported by preflight as not configured
        return None


def build_stt(settings: Settings) -> SpeechToText:
    if settings.stt_provider == "fixture":
        return FixtureSpeechToText()
    if settings.stt_provider == "azure":
        return AzureSpeechToText(settings.azure_speech_key, settings.azure_speech_region, settings.azure_stt_locale,
                                 token_provider=_speech_token_provider(settings), resource_id=settings.azure_speech_resource_id)
    return FasterWhisperSpeechToText(
        model_size=settings.local_stt_model, device=settings.local_stt_device,
        compute_type=settings.local_stt_compute_type, cache_dir=settings.resolve_path(settings.local_stt_cache_dir),
    )


def build_tts(settings: Settings) -> TextToSpeech:
    if settings.tts_provider == "fixture":
        return FixtureTextToSpeech()
    if settings.tts_provider == "azure":
        return AzureTextToSpeech(settings.azure_speech_key, settings.azure_speech_region, settings.azure_tts_voice,
                                 token_provider=_speech_token_provider(settings), resource_id=settings.azure_speech_resource_id)
    return PiperTextToSpeech(voice=settings.local_tts_voice, voices_dir=settings.resolve_path(settings.local_tts_voices_dir))


def build_blob(settings: Settings) -> BlobStore:
    if settings.blob_provider == "memory":
        return MemoryBlobStore()
    if settings.blob_provider == "azure":
        return AzureBlobStore(container=settings.blob_container, account_url=settings.azure_storage_account_url,
                              connection_string=settings.azure_storage_connection_string, name="azure-blob")
    return AzureBlobStore(container=settings.blob_container,
                          connection_string=settings.azure_storage_connection_string, name="azurite")


def video_mode(settings: Settings) -> str:
    """Which renderer `video_provider` resolves to: avatar | cards | fixture."""
    if settings.video_provider != "auto":
        return settings.video_provider
    if settings.tts_provider == "fixture":
        return "fixture"
    if settings.tts_provider == "azure":
        return "avatar"
    return "cards"


def build_video(settings: Settings, tts: TextToSpeech) -> VideoRenderer:
    mode = video_mode(settings)
    work_dir = (settings.resolve_path(settings.video_work_dir) if settings.video_work_dir
                else Path(tempfile.gettempdir()) / "dlp-video")
    if mode == "fixture":
        return SceneCardRenderer(FixtureTextToSpeech(), work_dir=work_dir, name="fixture", fast=True,
                                 timeout_seconds=settings.ffmpeg_timeout_seconds * 6,
                                 memory_limit_mb=settings.ffmpeg_memory_limit_mb)
    if mode == "avatar":
        return AzureAvatarRenderer(
            key=settings.azure_speech_key,
            endpoint=endpoint_for(endpoint=settings.azure_speech_endpoint, resource_id=settings.azure_speech_resource_id,
                                  region=settings.azure_speech_region),
            voice=settings.azure_tts_voice, character=settings.video_avatar_character, style=settings.video_avatar_style,
            background=settings.video_avatar_background, token_provider=_speech_token_provider(settings),
        )
    return SceneCardRenderer(tts, work_dir=work_dir, name="scene-cards", font=settings.video_font,
                             timeout_seconds=settings.ffmpeg_timeout_seconds * 9,
                             memory_limit_mb=settings.ffmpeg_memory_limit_mb)


def build_providers(settings: Settings | None = None) -> Providers:
    settings = settings or get_settings()
    tts = build_tts(settings)
    return Providers(
        chat=build_chat(settings, "small"),
        chat_strong=build_chat(settings, "strong"),
        stt=build_stt(settings),
        tts=tts,
        blob=build_blob(settings),
        video=build_video(settings, tts),
    )


@lru_cache(maxsize=1)
def get_providers() -> Providers:
    return build_providers()


def reset_providers() -> None:
    get_providers.cache_clear()
