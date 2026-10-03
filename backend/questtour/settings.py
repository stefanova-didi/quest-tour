from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str
    database_auth: Literal["password", "azure_ad"] = "password"
    host_id: str = "default"
    public_base_url: str
    storage_backend: Literal["azure", "local"] = "azure"
    azure_storage_connection_string: str | None = None
    azure_storage_account_url: str | None = None
    local_storage_dir: Path = Path(".storage")
    photos_container: str = "photos"
    images_container: str = "images"
    static_dir: Path | None = None
    max_photo_bytes: int = 20 * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
