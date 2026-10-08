from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from questtour.main import create_app
from questtour.settings import Settings


def test_settings_validates_admin_fields():
    settings = Settings(
        _env_file=None,
        database_url="sqlite://",
        public_base_url="http://test",
        admin_auth_provider="dev",
        admin_session_secret="a" * 32,
        admin_session_max_age_minutes=720,
        admin_session_secure=False,
        admin_dev_emails=["admin@example.com"],
        config_dir="config",
    )
    assert settings.admin_auth_provider == "dev"
    assert settings.admin_session_secret == "a" * 32
    assert settings.admin_session_max_age_minutes == 720
    assert settings.admin_session_secure is False
    assert settings.admin_dev_emails == ["admin@example.com"]
    assert settings.config_dir == Path("config")


def test_settings_rejects_short_session_secret():
    with pytest.raises(ValueError):
        Settings(
            _env_file=None,
            database_url="sqlite://",
            public_base_url="http://test",
            admin_session_secret="short",
        )


def test_settings_entra_requires_all_fields():
    with pytest.raises(ValueError):
        Settings(
            _env_file=None,
            database_url="sqlite://",
            public_base_url="http://test",
            admin_auth_provider="entra",
            admin_entra_tenant_id="tenant",
            # missing other entra fields
        )


def test_settings_splits_admin_dev_emails_from_string():
    settings = Settings(
        _env_file=None,
        database_url="sqlite://",
        public_base_url="http://test",
        admin_dev_emails="a@example.com,b@example.com",
    )
    assert settings.admin_dev_emails == ["a@example.com", "b@example.com"]


def test_settings_splits_admin_dev_emails_from_env(monkeypatch):
    # The env/.env source must honor the documented comma-separated format too,
    # not only values passed as init arguments.
    monkeypatch.setenv("ADMIN_DEV_EMAILS", "a@example.com,b@example.com")
    settings = Settings(
        _env_file=None,
        database_url="sqlite://",
        public_base_url="http://test",
    )
    assert settings.admin_dev_emails == ["a@example.com", "b@example.com"]


def test_create_app_exposes_seed_error_and_session_middleware(
    settings, session_factory, blob_store, clock
):
    # Point config_dir at a non-existent path so the seed lifespan does not run.
    settings.config_dir = settings.local_storage_dir / "no-config"

    app = create_app(settings, session_factory=session_factory, blob_store=blob_store, clock=clock)
    middleware_classes = [m.cls for m in app.user_middleware]
    assert SessionMiddleware in middleware_classes

    # TestClient enters the lifespan, which exposes seed_error on app.state.
    with TestClient(app):
        assert hasattr(app.state, "seed_error")
        assert app.state.seed_error is None
