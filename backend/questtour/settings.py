from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str
    database_auth: Literal["password", "azure_ad"] = "password"
    database_owner_role: str | None = None  # prod: NOLOGIN role that owns the tables (db-setup)
    host_id: str = "default"
    public_base_url: str
    storage_backend: Literal["azure", "local"] = "azure"
    azure_storage_connection_string: str | None = None
    azure_storage_account_url: str | None = None
    local_storage_dir: Path = Path(".storage")
    photos_container: str = "photos"
    images_container: str = "images"
    albums_container: str = "albums"  # stored memories-album PDFs (issue #33)
    static_dir: Path | None = None
    max_photo_bytes: int = 20 * 1024 * 1024
    # Version shown by /api/health; unset, the packaged VERSION file is used (questtour/version.py).
    app_version: str | None = None

    # Admin auth / session settings
    admin_auth_provider: Literal["entra", "dev"] = "dev"
    admin_session_secret: str = "dev-secret-do-not-use-in-production-with-claude-code"
    admin_session_max_age_minutes: int = 12 * 60
    admin_session_secure: bool = False

    admin_entra_tenant_id: str | None = None
    admin_entra_client_id: str | None = None
    admin_entra_client_secret: str | None = None
    admin_entra_redirect_uri: str | None = None
    admin_entra_group_object_id: str | None = None

    # NoDecode: the env source hands the raw string to _split_admin_dev_emails
    # (comma-separated per .env.example) instead of JSON-decoding it first.
    admin_dev_emails: Annotated[list[str], NoDecode] = []
    config_dir: Path = Path("config")

    @field_validator("admin_session_secret")
    @classmethod
    def _validate_admin_session_secret(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("admin_session_secret must be at least 32 characters")
        return value

    @field_validator("admin_dev_emails", mode="before")
    @classmethod
    def _split_admin_dev_emails(cls, value):
        if isinstance(value, str):
            return [email.strip() for email in value.split(",") if email.strip()]
        return value

    @model_validator(mode="after")
    def _validate_entra_config(self):
        if self.admin_auth_provider == "entra":
            missing = []
            for field in (
                "admin_entra_tenant_id",
                "admin_entra_client_id",
                "admin_entra_client_secret",
                "admin_entra_redirect_uri",
                "admin_entra_group_object_id",
            ):
                if not getattr(self, field):
                    missing.append(field)
            if missing:
                raise ValueError(f"admin_auth_provider='entra' requires: {', '.join(missing)}")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
