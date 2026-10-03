import os
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from questtour import models  # noqa: F401
from questtour.db import Base
from questtour.settings import Settings
from questtour.storage import LocalBlobStore
from tests.factories import seed_game


class FakeClock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now

    def advance(self, **delta) -> None:
        self.now += timedelta(**delta)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(datetime(2026, 10, 14, 8, 0, tzinfo=UTC))  # 11:00 in Europe/Sofia


@pytest.fixture
def engine():
    url = os.environ.get("TEST_DATABASE_URL")
    if url:
        eng = create_engine(url)
        Base.metadata.drop_all(eng)
    else:
        eng = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session_factory(engine):
    return sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
def blob_store(tmp_path) -> LocalBlobStore:
    return LocalBlobStore(tmp_path / "blobs")


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        _env_file=None,
        database_url="sqlite://",
        public_base_url="http://test",
        storage_backend="local",
        local_storage_dir=tmp_path / "blobs",
        static_dir=None,
    )


@pytest.fixture
def app(settings, session_factory, blob_store, clock):
    # Imported here so the infrastructure collects before the API layer exists.
    from questtour.main import create_app

    return create_app(
        settings, session_factory=session_factory, blob_store=blob_store, clock=clock
    )


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app, headers={"X-Device-Id": "device-aaaa-0001"})


@pytest.fixture
def seed(session_factory, clock):
    with session_factory() as session:
        return seed_game(session, clock.now)
