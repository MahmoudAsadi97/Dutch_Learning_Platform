"""The only package that talks to external services (models, speech, storage).

Each interface in `base.py` has a local development implementation, a fixture
implementation for CI and failure injection, and (from M3) an Azure implementation.
`registry.py` selects them from configuration; `preflight.py` reports what is
configured without printing secrets.
"""

from dlp.providers.base import (
    AudioResult,
    BlobStore,
    ChatMessage,
    ChatModel,
    ChatResult,
    ProviderError,
    ProviderUnavailable,
    SpeechToText,
    TextToSpeech,
    Transcript,
)

__all__ = [
    "AudioResult",
    "BlobStore",
    "ChatMessage",
    "ChatModel",
    "ChatResult",
    "ProviderError",
    "ProviderUnavailable",
    "SpeechToText",
    "TextToSpeech",
    "Transcript",
]
