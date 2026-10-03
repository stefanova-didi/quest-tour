from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from questtour.settings import Settings


class BlobExists(Exception):
    pass


class StorageUnavailable(Exception):
    pass


class BlobStore(Protocol):
    def ensure_container(self, container: str) -> None: ...

    def exists(self, container: str, name: str) -> bool: ...

    def put(
        self, container: str, name: str, data: bytes, content_type: str, *, overwrite: bool
    ) -> None: ...

    def get(self, container: str, name: str) -> tuple[bytes, str] | None: ...


class LocalBlobStore:
    """Filesystem store for tests and the no-Docker dev fallback."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def _path(self, container: str, name: str) -> Path:
        return self.root / container / name

    def ensure_container(self, container: str) -> None:
        (self.root / container).mkdir(parents=True, exist_ok=True)

    def exists(self, container: str, name: str) -> bool:
        return self._path(container, name).is_file()

    def put(self, container, name, data, content_type, *, overwrite):
        path = self._path(container, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("wb" if overwrite else "xb") as fh:
                fh.write(data)
        except FileExistsError as exc:
            raise BlobExists(name) from exc
        path.with_name(path.name + ".content-type").write_text(content_type, encoding="utf-8")

    def get(self, container, name):
        path = self._path(container, name)
        if not path.is_file():
            return None
        ctype_file = path.with_name(path.name + ".content-type")
        ctype = (
            ctype_file.read_text(encoding="utf-8")
            if ctype_file.exists()
            else "application/octet-stream"
        )
        return path.read_bytes(), ctype


class AzureBlobStore:
    def __init__(self, service) -> None:  # azure.storage.blob.BlobServiceClient
        self.service = service

    def ensure_container(self, container):
        from azure.core.exceptions import ResourceExistsError

        try:
            self.service.create_container(container)
        except ResourceExistsError:
            pass

    def exists(self, container, name):
        return self.service.get_blob_client(container, name).exists()

    def put(self, container, name, data, content_type, *, overwrite):
        from azure.core.exceptions import AzureError, ResourceExistsError
        from azure.storage.blob import ContentSettings

        try:
            self.service.get_blob_client(container, name).upload_blob(
                data,
                overwrite=overwrite,
                content_settings=ContentSettings(content_type=content_type),
            )
        except ResourceExistsError as exc:
            raise BlobExists(name) from exc
        except AzureError as exc:
            raise StorageUnavailable(str(exc)) from exc

    def get(self, container, name):
        from azure.core.exceptions import ResourceNotFoundError

        blob = self.service.get_blob_client(container, name)
        try:
            downloader = blob.download_blob()
        except ResourceNotFoundError:
            return None
        return downloader.readall(), downloader.properties.content_settings.content_type


def make_blob_store(settings: Settings) -> BlobStore:
    if settings.storage_backend == "local":
        return LocalBlobStore(settings.local_storage_dir)
    from azure.storage.blob import BlobServiceClient

    # The photo upload runs while the team's run row is locked: keep SDK retries short so a storage
    # outage fails fast (503 -> client Retry) instead of stalling teammates' requests for minutes.
    client_options = {"retry_total": 2, "connection_timeout": 10, "read_timeout": 60}
    if settings.azure_storage_connection_string:
        return AzureBlobStore(
            BlobServiceClient.from_connection_string(
                settings.azure_storage_connection_string, **client_options
            )
        )
    if not settings.azure_storage_account_url:
        raise RuntimeError("Set AZURE_STORAGE_CONNECTION_STRING or AZURE_STORAGE_ACCOUNT_URL")
    from azure.identity import DefaultAzureCredential

    return AzureBlobStore(
        BlobServiceClient(
            settings.azure_storage_account_url,
            credential=DefaultAzureCredential(),
            **client_options,
        )
    )
