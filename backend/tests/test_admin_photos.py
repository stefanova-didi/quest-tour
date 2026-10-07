from datetime import UTC, datetime
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.middleware.sessions import SessionMiddleware

from questtour.admin import admin_router
from questtour.admin.errors import register_admin_exception_handlers
from questtour.api import play
from questtour.auth import auth_router
from questtour.db import Base
from questtour.models import Assignment, GameRun, Landmark, Photo, RunTask
from questtour.settings import Settings
from questtour.storage import LocalBlobStore
from tests.factories import seed_game

JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
TXT = b"not an image"


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        _env_file=None,
        database_url="sqlite://",
        public_base_url="http://test",
        storage_backend="local",
        local_storage_dir=tmp_path / "blobs",
        static_dir=None,
        admin_session_secret="test-secret-must-be-at-least-32-bytes-long",
        admin_auth_provider="dev",
        admin_dev_emails=["admin@example.com"],
    )


@pytest.fixture
def engine():
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
def clock():
    class FakeClock:
        def __init__(self):
            self.now = datetime(2026, 10, 14, 8, 0, tzinfo=UTC)

        def __call__(self) -> datetime:
            return self.now

        def advance(self, **delta):
            self.now += __import__("datetime").timedelta(**delta)

    return FakeClock()


@pytest.fixture
def seed(session_factory, clock):
    with session_factory() as session:
        return seed_game(session, clock.now)


@pytest.fixture
def admin_app(settings, session_factory, blob_store, clock):
    app = FastAPI()
    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.blob_store = blob_store
    app.state.clock = clock
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.admin_session_secret,
        session_cookie="questtour_admin_session",
        max_age=settings.admin_session_max_age_minutes * 60,
        same_site="lax",
        https_only=settings.admin_session_secure,
    )
    register_admin_exception_handlers(app)
    app.include_router(auth_router)
    app.include_router(admin_router)
    app.include_router(play.router)
    return app


@pytest.fixture
def admin_client(admin_app) -> TestClient:
    return TestClient(admin_app, raise_server_exceptions=False)


@pytest.fixture
def player_client(admin_app) -> TestClient:
    return TestClient(admin_app, headers={"X-Device-Id": "device-aaaa-0001"})


def _login(client: TestClient) -> None:
    request_resp = client.post("/api/admin/auth/magic/request", json={"email": "admin@example.com"})
    assert request_resp.status_code == 200
    parsed = urlparse(request_resp.json()["url"])
    params = parse_qs(parsed.query)
    verify_resp = client.get(
        "/api/admin/auth/magic/verify",
        params={"token": params["token"][0], "email": params["email"][0]},
        follow_redirects=False,
    )
    assert verify_resp.status_code == 307


def _landmark_id(session_factory, seed) -> int:
    with session_factory() as session:
        game = session.get(Assignment, seed.assignment_id).game
        return game.tasks[0].landmark_id


def _seeded_landmark(session_factory, seed) -> Landmark:
    with session_factory() as session:
        return session.get(Landmark, _landmark_id(session_factory, seed))


def _player_upload_photo(client: TestClient, token: str):
    client.post(f"/api/play/{token}/start")
    client.post(f"/api/play/{token}/answer", json={"position": 0, "answer": "Alexander Nevsky"})
    resp = client.post(
        f"/api/play/{token}/photo",
        data={"position": "0"},
        files={"file": ("p.jpg", JPEG, "image/jpeg")},
    )
    assert resp.status_code == 200
    return resp


def test_upload_landmark_picture_updates_task_image(
    session_factory, seed, admin_client, blob_store
):
    _login(admin_client)
    landmark_id = _landmark_id(session_factory, seed)

    resp = admin_client.post(
        f"/api/admin/landmarks/{landmark_id}/pictures",
        data={"kind": "task"},
        files={"file": ("pic.jpg", JPEG, "image/jpeg")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["blob_name"].endswith(".jpg")
    assert data["url"] == f"http://test/api/images/{data['blob_name']}"
    assert blob_store.exists("images", data["blob_name"])

    with session_factory() as session:
        lm = session.get(Landmark, landmark_id)
        assert lm.task_image == data["blob_name"]


def test_upload_landmark_picture_updates_info_image(
    session_factory, seed, admin_client, blob_store
):
    _login(admin_client)
    landmark_id = _landmark_id(session_factory, seed)

    resp = admin_client.post(
        f"/api/admin/landmarks/{landmark_id}/pictures",
        data={"kind": "info"},
        files={"file": ("pic.png", PNG, "image/png")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["blob_name"].endswith(".png")
    assert blob_store.exists("images", data["blob_name"])

    with session_factory() as session:
        lm = session.get(Landmark, landmark_id)
        assert lm.info_image == data["blob_name"]


def test_upload_landmark_picture_replaces_old_blob(session_factory, seed, admin_client, blob_store):
    _login(admin_client)
    landmark_id = _landmark_id(session_factory, seed)

    first = admin_client.post(
        f"/api/admin/landmarks/{landmark_id}/pictures",
        data={"kind": "task"},
        files={"file": ("pic.jpg", JPEG, "image/jpeg")},
    )
    first_blob = first.json()["blob_name"]
    assert blob_store.exists("images", first_blob)

    second = admin_client.post(
        f"/api/admin/landmarks/{landmark_id}/pictures",
        data={"kind": "task"},
        files={"file": ("pic2.jpg", JPEG + b"extra", "image/jpeg")},
    )
    second_blob = second.json()["blob_name"]
    assert second_blob != first_blob
    assert blob_store.exists("images", second_blob)
    assert not blob_store.exists("images", first_blob)


def test_upload_landmark_picture_same_bytes_keeps_blob(session_factory, seed, admin_client, blob_store):
    _login(admin_client)
    landmark_id = _landmark_id(session_factory, seed)

    first = admin_client.post(
        f"/api/admin/landmarks/{landmark_id}/pictures",
        data={"kind": "task"},
        files={"file": ("pic.jpg", JPEG, "image/jpeg")},
    )
    first_blob = first.json()["blob_name"]
    assert blob_store.exists("images", first_blob)

    second = admin_client.post(
        f"/api/admin/landmarks/{landmark_id}/pictures",
        data={"kind": "task"},
        files={"file": ("pic.jpg", JPEG, "image/jpeg")},
    )
    second_blob = second.json()["blob_name"]
    assert second_blob == first_blob
    assert blob_store.exists("images", second_blob)

    with session_factory() as session:
        lm = session.get(Landmark, landmark_id)
        assert lm.task_image == second_blob


def test_upload_landmark_picture_rejects_unsupported_type(session_factory, seed, admin_client):
    _login(admin_client)
    landmark_id = _landmark_id(session_factory, seed)

    resp = admin_client.post(
        f"/api/admin/landmarks/{landmark_id}/pictures",
        data={"kind": "task"},
        files={"file": ("pic.txt", TXT, "text/plain")},
    )
    assert resp.status_code == 422
    errors = resp.json()["errors"]
    assert any(e["field"] == "file" and "unsupported image type" in e["message"] for e in errors)


def test_upload_landmark_picture_rejects_invalid_kind(session_factory, seed, admin_client):
    _login(admin_client)
    landmark_id = _landmark_id(session_factory, seed)

    resp = admin_client.post(
        f"/api/admin/landmarks/{landmark_id}/pictures",
        data={"kind": "other"},
        files={"file": ("pic.jpg", JPEG, "image/jpeg")},
    )
    assert resp.status_code == 422
    errors = resp.json()["errors"]
    assert any(e["field"] == "kind" and "kind must be" in e["message"] for e in errors)


def test_upload_landmark_picture_preserves_blob_referenced_by_other_landmark(
    session_factory, seed, admin_client, blob_store
):
    _login(admin_client)
    landmark_a_id = _landmark_id(session_factory, seed)

    with session_factory() as session:
        landmark_b = Landmark(
            host_id=session.get(Landmark, landmark_a_id).host_id,
            key="other-landmark",
            name="Other Landmark",
            task_text="Task B",
            accepted_answers=["B"],
            info_text="Info B",
        )
        session.add(landmark_b)
        session.commit()
        landmark_b_id = landmark_b.id

    first = admin_client.post(
        f"/api/admin/landmarks/{landmark_a_id}/pictures",
        data={"kind": "task"},
        files={"file": ("pic.jpg", JPEG, "image/jpeg")},
    )
    shared_blob = first.json()["blob_name"]
    assert blob_store.exists("images", shared_blob)

    # Same bytes uploaded to a second landmark share the same blob.
    second = admin_client.post(
        f"/api/admin/landmarks/{landmark_b_id}/pictures",
        data={"kind": "task"},
        files={"file": ("pic.jpg", JPEG, "image/jpeg")},
    )
    assert second.json()["blob_name"] == shared_blob

    # Replacing landmark A's picture must not delete the blob still used by B.
    replacement = admin_client.post(
        f"/api/admin/landmarks/{landmark_a_id}/pictures",
        data={"kind": "task"},
        files={"file": ("pic2.jpg", JPEG + b"extra", "image/jpeg")},
    )
    new_blob = replacement.json()["blob_name"]
    assert new_blob != shared_blob
    assert blob_store.exists("images", new_blob)
    assert blob_store.exists("images", shared_blob)

    with session_factory() as session:
        b = session.get(Landmark, landmark_b_id)
        assert b.task_image == shared_blob


def test_upload_landmark_picture_rejects_oversized_file(session_factory, seed, admin_client):
    _login(admin_client)
    landmark_id = _landmark_id(session_factory, seed)

    oversize = b"\xff\xd8\xff\xe0" + b"\x00" * (30 * 1024 * 1024)
    resp = admin_client.post(
        f"/api/admin/landmarks/{landmark_id}/pictures",
        data={"kind": "task"},
        files={"file": ("big.jpg", oversize, "image/jpeg")},
    )
    assert resp.status_code == 422
    errors = resp.json()["errors"]
    assert any(e["field"] == "file" and "exceeds" in e["message"] for e in errors)


def test_upload_landmark_picture_returns_404_for_unknown_landmark(admin_client):
    _login(admin_client)
    resp = admin_client.post(
        "/api/admin/landmarks/99999/pictures",
        data={"kind": "task"},
        files={"file": ("pic.jpg", JPEG, "image/jpeg")},
    )
    assert resp.status_code == 404


def test_list_team_photos(session_factory, seed, player_client, admin_client):
    _player_upload_photo(player_client, seed.token)
    photo_id = _photo_id_for_upload(session_factory, seed)

    _login(admin_client)
    resp = admin_client.get("/api/admin/photos")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == photo_id
    assert data[0]["team_name"] == "The Explorers"
    assert data[0]["game_name"] == "Sofia Old Town Quest"
    assert data[0]["url"] == f"http://test/api/admin/photos/{photo_id}/download"


def test_list_team_photos_filters_by_team_and_game(
    session_factory, seed, player_client, admin_client
):
    _player_upload_photo(player_client, seed.token)
    _player_upload_photo(player_client, seed.other_token)

    with session_factory() as session:
        team_id = session.get(Assignment, seed.assignment_id).team_id
        game_id = session.get(Assignment, seed.assignment_id).game_id

    _login(admin_client)
    by_team = admin_client.get("/api/admin/photos", params={"team_id": team_id}).json()
    assert len(by_team) == 1
    assert by_team[0]["team_name"] == "The Explorers"

    by_game = admin_client.get("/api/admin/photos", params={"game_id": game_id}).json()
    assert len(by_game) == 2

    other_team_id = 99999
    empty = admin_client.get("/api/admin/photos", params={"team_id": other_team_id}).json()
    assert empty == []


def test_list_team_photos_excludes_deleted(session_factory, seed, player_client, admin_client):
    _player_upload_photo(player_client, seed.token)
    photo_id = _photo_id_for_upload(session_factory, seed)

    _login(admin_client)
    assert len(admin_client.get("/api/admin/photos").json()) == 1

    admin_client.delete(f"/api/admin/photos/{photo_id}")
    assert admin_client.get("/api/admin/photos").json() == []


def test_delete_team_photo_decrements_count_and_bumps_version(
    session_factory, seed, player_client, admin_client
):
    _player_upload_photo(player_client, seed.token)
    photo_id = _photo_id_for_upload(session_factory, seed)

    with session_factory() as session:
        run_task = _run_task_for_photo(session, photo_id)
        run = session.get(GameRun, run_task.run_id)
        version_before = run.version
        assert run_task.photo_count == 1

    _login(admin_client)
    resp = admin_client.delete(f"/api/admin/photos/{photo_id}")
    assert resp.status_code == 200
    assert resp.json() == {"deleted": True}

    with session_factory() as session:
        photo = session.get(Photo, photo_id)
        assert photo.deleted_at is not None
        run_task = session.get(RunTask, photo.run_task_id)
        assert run_task.photo_count == 0
        assert session.get(GameRun, run_task.run_id).version == version_before + 1


def test_delete_team_photo_404_for_deleted_or_unknown(
    session_factory, seed, player_client, admin_client
):
    _player_upload_photo(player_client, seed.token)
    photo_id = _photo_id_for_upload(session_factory, seed)

    _login(admin_client)
    assert admin_client.delete(f"/api/admin/photos/{photo_id}").status_code == 200
    assert admin_client.delete(f"/api/admin/photos/{photo_id}").status_code == 404
    assert admin_client.delete("/api/admin/photos/99999").status_code == 404


def test_download_team_photo(session_factory, seed, player_client, admin_client):
    _player_upload_photo(player_client, seed.token)
    photo_id = _photo_id_for_upload(session_factory, seed)

    _login(admin_client)
    resp = admin_client.get(f"/api/admin/photos/{photo_id}/download")
    assert resp.status_code == 200
    assert resp.content == JPEG
    assert resp.headers["content-type"] == "image/jpeg"


def test_download_team_photo_404_for_deleted(session_factory, seed, player_client, admin_client):
    _player_upload_photo(player_client, seed.token)
    photo_id = _photo_id_for_upload(session_factory, seed)

    _login(admin_client)
    admin_client.delete(f"/api/admin/photos/{photo_id}")
    assert admin_client.get(f"/api/admin/photos/{photo_id}/download").status_code == 404


def test_player_photo_count_ignores_deleted_photo(
    session_factory, seed, player_client, admin_client
):
    _player_upload_photo(player_client, seed.token)
    photo_id = _photo_id_for_upload(session_factory, seed)

    state = player_client.get(f"/api/play/{seed.token}").json()
    assert state["phase"] == "info"
    assert state["task"]["photo_count"] == 1

    _login(admin_client)
    admin_client.delete(f"/api/admin/photos/{photo_id}")

    state = player_client.get(f"/api/play/{seed.token}").json()
    assert state["phase"] == "photo"
    assert state["task"]["photo_count"] == 0

    # The team can upload a replacement photo for the same completed task.
    resp = player_client.post(
        f"/api/play/{seed.token}/photo",
        data={"position": "0"},
        files={"file": ("p2.jpg", JPEG + b"x", "image/jpeg")},
    )
    assert resp.status_code == 200

    state = player_client.get(f"/api/play/{seed.token}").json()
    assert state["task"]["photo_count"] == 1


def _photo_id_for_upload(session_factory, seed) -> int:
    with session_factory() as session:
        assignment = session.get(Assignment, seed.assignment_id)
        run = session.scalar(select(GameRun).where(GameRun.assignment_id == assignment.id))
        task = next(t for t in run.tasks if t.position == 0)
        photo = session.scalar(select(Photo).where(Photo.run_task_id == task.id))
        return photo.id


def _run_task_for_photo(session, photo_id: int) -> RunTask:
    photo = session.get(Photo, photo_id)
    return session.get(RunTask, photo.run_task_id)
