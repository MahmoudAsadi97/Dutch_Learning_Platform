"""Blob storage through the Azure SDK. Azurite (Phase A) and Azure Blob Storage (Phase B) share it."""

from __future__ import annotations

import re
from typing import Any

from dlp.providers.base import BlobStore, ProviderError, ProviderUnavailable

KEY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,299}$")


def validate_key(key: str) -> str:
    if not KEY_PATTERN.match(key) or ".." in key:
        raise ValueError(f"invalid blob key: {key!r}")
    return key


class AzureBlobStore(BlobStore):
    def __init__(self, *, container: str, connection_string: str = "", account_url: str = "",
                 name: str = "azurite") -> None:
        self.name = name
        self.container = container
        self.connection_string = connection_string
        self.account_url = account_url
        self._client: Any = None

    def _container(self) -> Any:
        if self._client is None:
            try:
                from azure.storage.blob import BlobServiceClient
            except ImportError as exc:
                raise ProviderUnavailable("azure-storage-blob is not installed") from exc
            if self.connection_string:
                service = BlobServiceClient.from_connection_string(self.connection_string)
            elif self.account_url:
                from azure.identity import DefaultAzureCredential

                service = BlobServiceClient(account_url=self.account_url, credential=DefaultAzureCredential())
            else:
                raise ProviderUnavailable("no blob storage connection configured")
            container = service.get_container_client(self.container)
            try:
                if not container.exists():
                    container.create_container()
            except Exception as exc:  # noqa: BLE001
                raise ProviderError(f"cannot reach blob storage: {exc.__class__.__name__}") from exc
            self._client = container
        return self._client

    def put(self, key: str, data: bytes, *, content_type: str = "application/octet-stream") -> None:
        from azure.storage.blob import ContentSettings

        blob = self._container().get_blob_client(validate_key(key))
        try:
            blob.upload_blob(data, overwrite=True, content_settings=ContentSettings(content_type=content_type))
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"blob upload failed: {exc.__class__.__name__}") from exc

    def get(self, key: str) -> bytes:
        blob = self._container().get_blob_client(validate_key(key))
        try:
            return blob.download_blob().readall()
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"blob download failed: {exc.__class__.__name__}") from exc

    def exists(self, key: str) -> bool:
        key = validate_key(key)
        try:
            return bool(self._container().get_blob_client(key).exists())
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"blob lookup failed: {exc.__class__.__name__}") from exc

    def delete(self, key: str) -> None:
        blob = self._container().get_blob_client(validate_key(key))
        try:
            if blob.exists():
                blob.delete_blob()
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"blob deletion failed: {exc.__class__.__name__}") from exc

    def ping(self) -> tuple[bool, str]:
        try:
            self._container()
            return True, f"container {self.container} reachable"
        except Exception as exc:  # noqa: BLE001
            return False, str(exc)
