import socket
import uuid

import pytest

from dlp.providers.blob_azure import AzureBlobStore, validate_key
from dlp.providers.fixtures import MemoryBlobStore

AZURITE_CONNECTION_STRING = (
    "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
    "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
    "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
)


def _azurite_running() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", 10000), timeout=0.5):
            return True
    except OSError:
        return False


def test_memory_store_round_trip():
    store = MemoryBlobStore()
    store.put("recordings/a/b.wav", b"abc", content_type="audio/wav")
    assert store.exists("recordings/a/b.wav") and store.get("recordings/a/b.wav") == b"abc"
    store.delete("recordings/a/b.wav")
    assert not store.exists("recordings/a/b.wav")


@pytest.mark.parametrize("bad", ["", "../etc/passwd", "a/../b", "/absolute", "sp ace", "x" * 400])
def test_blob_keys_are_validated(bad):
    with pytest.raises(ValueError):
        validate_key(bad)


@pytest.mark.azurite
@pytest.mark.skipif(not _azurite_running(), reason="Azurite is not listening on 127.0.0.1:10000")
def test_azurite_round_trip_through_the_azure_sdk():
    store = AzureBlobStore(container=f"test-{uuid.uuid4().hex[:8]}", connection_string=AZURITE_CONNECTION_STRING)
    ok, detail = store.ping()
    assert ok, detail
    key = f"recordings/{uuid.uuid4()}/turn.wav"
    store.put(key, b"RIFF....", content_type="audio/wav")
    assert store.exists(key)
    assert store.get(key) == b"RIFF...."
    store.delete(key)
    assert not store.exists(key)
