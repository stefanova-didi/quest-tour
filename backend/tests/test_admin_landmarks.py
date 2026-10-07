from datetime import UTC, datetime
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.middleware.sessions import SessionMiddleware

from questtour.admin import admin_router
from questtour.admin.errors import register_admin_exception_handlers
from questtour.auth import auth_router
from questtour.db import Base
from questtour.models import Assignment, Game, GameRun, GameTask, RunTask, Team
from questtour.settings import Settings
from questtour.storage import LocalBlobStore


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
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
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
def admin_app(settings, session_factory, blob_store):
    app = FastAPI()
    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.blob_store = blob_store
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
    return app


@pytest.fixture
def admin_client(admin_app) -> TestClient:
    return TestClient(admin_app, raise_server_exceptions=False)


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


def test_create_landmark_returns_structured_data(admin_client):
    _login(admin_client)
    payload = {
        "key": "cathedral",
        "name": "Cathedral",
        "task": "Find the west door.",
        "accepted_answers": ["west door"],
        "tourist_info": "Built in the 19th century.",
    }
    resp = admin_client.post("/api/admin/landmarks", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["key"] == "cathedral"
    assert data["name"] == "Cathedral"
    assert data["task"] == "Find the west door."
    assert data["accepted_answers"] == ["west door"]
    assert data["tourist_info"] == "Built in the 19th century."
    assert data["coordinates"] is None
    assert "task_image_url" in data
    assert "info_image_url" in data
    assert "updated_at" in data


def test_create_landmark_with_coordinates(admin_client):
    _login(admin_client)
    payload = {
        "key": "theatre",
        "name": "Theatre",
        "task": "Find the main entrance.",
        "accepted_answers": ["main entrance"],
        "tourist_info": "National theatre.",
        "coordinates": {"lat": 42.6947, "lon": 23.3246},
    }
    resp = admin_client.post("/api/admin/landmarks", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["coordinates"] == {"lat": pytest.approx(42.6947), "lon": pytest.approx(23.3246)}


def test_create_landmark_reuses_schema_validation_rules(admin_client):
    _login(admin_client)
    # hint2 without hint1 should be rejected.
    payload = {
        "key": "invalid-hints",
        "name": "Invalid hints",
        "task": "Task text.",
        "accepted_answers": ["answer"],
        "hint2": "this should fail",
        "tourist_info": "Info text.",
    }
    resp = admin_client.post("/api/admin/landmarks", json=payload)
    assert resp.status_code == 422
    data = resp.json()
    assert "errors" in data
    assert any("hint2" in e["field"] or "hint2" in e["message"] for e in data["errors"])


def test_create_landmark_rejects_blank_answer_after_normalisation(admin_client):
    _login(admin_client)
    payload = {
        "key": "blank-answer",
        "name": "Blank answer",
        "task": "Task text.",
        "accepted_answers": ["   "],
        "tourist_info": "Info text.",
    }
    resp = admin_client.post("/api/admin/landmarks", json=payload)
    assert resp.status_code == 422
    assert "errors" in resp.json()


def test_duplicate_key_returns_422_field_error(admin_client):
    _login(admin_client)
    payload = {
        "key": "duplicate",
        "name": "Duplicate",
        "task": "Task.",
        "accepted_answers": ["answer"],
        "tourist_info": "Info.",
    }
    assert admin_client.post("/api/admin/landmarks", json=payload).status_code == 201
    resp = admin_client.post("/api/admin/landmarks", json=payload)
    assert resp.status_code == 422
    data = resp.json()
    assert "errors" in data
    assert any(e["field"] == "key" for e in data["errors"])


def test_list_landmarks_with_optional_filter(admin_client):
    _login(admin_client)
    for key, name in [("alpha", "Alpha Landmark"), ("beta", "Beta Landmark")]:
        admin_client.post(
            "/api/admin/landmarks",
            json={
                "key": key,
                "name": name,
                "task": "Task.",
                "accepted_answers": ["answer"],
                "tourist_info": "Info.",
            },
        )
    resp = admin_client.get("/api/admin/landmarks")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["name"] == "Alpha Landmark"

    filtered = admin_client.get("/api/admin/landmarks?q=Beta")
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1
    assert filtered.json()[0]["name"] == "Beta Landmark"


def test_get_landmark_by_id(admin_client):
    _login(admin_client)
    create_resp = admin_client.post(
        "/api/admin/landmarks",
        json={
            "key": "get-by-id",
            "name": "Get by ID",
            "task": "Task.",
            "accepted_answers": ["answer"],
            "tourist_info": "Info.",
        },
    )
    landmark_id = create_resp.json()["id"]
    resp = admin_client.get(f"/api/admin/landmarks/{landmark_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == landmark_id


def test_get_unknown_landmark_returns_404(admin_client):
    _login(admin_client)
    resp = admin_client.get("/api/admin/landmarks/9999")
    assert resp.status_code == 404


def test_update_landmark_returns_structured_data(admin_client):
    _login(admin_client)
    create_resp = admin_client.post(
        "/api/admin/landmarks",
        json={
            "key": "update-me",
            "name": "Update me",
            "task": "Task.",
            "accepted_answers": ["answer"],
            "tourist_info": "Info.",
        },
    )
    landmark_id = create_resp.json()["id"]
    payload = {
        "key": "updated-key",
        "name": "Updated name",
        "task": "Updated task.",
        "accepted_answers": ["updated"],
        "tourist_info": "Updated info.",
    }
    resp = admin_client.put(f"/api/admin/landmarks/{landmark_id}", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["key"] == "updated-key"
    assert data["name"] == "Updated name"


def test_update_landmark_with_stale_seen_at_returns_409(admin_client):
    _login(admin_client)
    create_resp = admin_client.post(
        "/api/admin/landmarks",
        json={
            "key": "stale-update",
            "name": "Stale update",
            "task": "Task.",
            "accepted_answers": ["answer"],
            "tourist_info": "Info.",
        },
    )
    landmark_id = create_resp.json()["id"]
    stale = datetime(2020, 1, 1, tzinfo=UTC).isoformat()
    payload = {
        "key": "stale-update",
        "name": "Updated",
        "task": "Task.",
        "accepted_answers": ["answer"],
        "tourist_info": "Info.",
        "seen_at": stale,
    }
    resp = admin_client.put(f"/api/admin/landmarks/{landmark_id}", json=payload)
    assert resp.status_code == 409
    data = resp.json()
    assert data["entity"] == "Landmark"
    assert "current" in data


def test_delete_landmark_blocked_by_any_run_task_reference(admin_client, session_factory):
    _login(admin_client)
    create_resp = admin_client.post(
        "/api/admin/landmarks",
        json={
            "key": "run-referenced",
            "name": "Run referenced",
            "task": "Task.",
            "accepted_answers": ["answer"],
            "tourist_info": "Info.",
        },
    )
    landmark_id = create_resp.json()["id"]
    with session_factory() as session:
        team = Team(host_id="default", key="team", name="Team")
        game = Game(
            host_id="default",
            key="game",
            name="Game",
            intro="Intro",
            time_zone="Europe/Sofia",
            max_duration_minutes=60,
            reveal_after_attempts=5,
            reveal_after_minutes=20,
            reveal_penalty_minutes=30,
        )
        assignment = Assignment(
            host_id="default",
            team=team,
            game=game,
            valid_from=datetime.now(UTC),
            valid_until=datetime.now(UTC),
            exit_message="",
        )
        session.add_all([team, game, assignment])
        session.flush()
        run = GameRun(assignment_id=assignment.id, started_at=datetime.now(UTC), current_position=0, version=1)
        session.add(run)
        session.flush()
        run_task = RunTask(
            run_id=run.id,
            position=0,
            landmark_id=landmark_id,
            hint_penalty_minutes=0,
            reveal_penalty_minutes=0,
            wrong_attempts=0,
            photo_count=0,
        )
        session.add(run_task)
        session.commit()

    resp = admin_client.delete(f"/api/admin/landmarks/{landmark_id}")
    assert resp.status_code == 409
    assert "run" in resp.json()["detail"].lower()


def test_delete_landmark_blocked_by_game_task_unless_forced(admin_client, session_factory):
    _login(admin_client)
    create_resp = admin_client.post(
        "/api/admin/landmarks",
        json={
            "key": "game-referenced",
            "name": "Game referenced",
            "task": "Task.",
            "accepted_answers": ["answer"],
            "tourist_info": "Info.",
        },
    )
    landmark_id = create_resp.json()["id"]
    with session_factory() as session:
        game = Game(
            host_id="default",
            key="game2",
            name="Game 2",
            intro="Intro",
            time_zone="Europe/Sofia",
            max_duration_minutes=60,
            reveal_after_attempts=5,
            reveal_after_minutes=20,
            reveal_penalty_minutes=30,
        )
        session.add(game)
        session.flush()
        session.add(GameTask(game_id=game.id, position=0, landmark_id=landmark_id))
        session.commit()

    resp = admin_client.delete(f"/api/admin/landmarks/{landmark_id}")
    assert resp.status_code == 409
    data = resp.json()
    assert "used_by_games" in data
    assert game.id in data["used_by_games"]

    force_resp = admin_client.delete(f"/api/admin/landmarks/{landmark_id}?force=true")
    assert force_resp.status_code == 200
    assert force_resp.json() == {"deleted": True}


def test_delete_landmark_succeeds_when_unused(admin_client):
    _login(admin_client)
    create_resp = admin_client.post(
        "/api/admin/landmarks",
        json={
            "key": "delete-me",
            "name": "Delete me",
            "task": "Task.",
            "accepted_answers": ["answer"],
            "tourist_info": "Info.",
        },
    )
    landmark_id = create_resp.json()["id"]
    resp = admin_client.delete(f"/api/admin/landmarks/{landmark_id}")
    assert resp.status_code == 200
    assert resp.json() == {"deleted": True}


def test_create_landmark_with_i18n(admin_client):
    _login(admin_client)
    payload = {
        "key": "i18n-lm",
        "name": "Base",
        "name_i18n": {"de": "DE"},
        "task": "Task",
        "task_i18n": {"de": "DE task"},
        "accepted_answers": ["1"],
        "hint1": "Hint 1",
        "hint1_i18n": {"de": "DE hint1"},
        "tourist_info": "Info",
        "tourist_info_i18n": {"de": "DE info"},
    }
    res = admin_client.post("/api/admin/landmarks", json=payload)
    assert res.status_code == 201
    body = res.json()
    assert body["name_i18n"] == {"de": "DE"}
    assert body["task_i18n"] == {"de": "DE task"}
    assert body["hint1_i18n"] == {"de": "DE hint1"}
    assert body["tourist_info_i18n"] == {"de": "DE info"}


def test_create_landmark_rejects_blank_i18n_value(admin_client):
    _login(admin_client)
    payload = {
        "key": "blank-i18n",
        "name": "Base",
        "name_i18n": {"de": ""},
        "task": "Task",
        "accepted_answers": ["1"],
        "tourist_info": "Info",
    }
    res = admin_client.post("/api/admin/landmarks", json=payload)
    assert res.status_code == 422
    assert "errors" in res.json()


def test_create_landmark_rejects_hint1_i18n_without_hint1(admin_client):
    _login(admin_client)
    payload = {
        "key": "hint1-i18n-only",
        "name": "Base",
        "task": "Task",
        "accepted_answers": ["1"],
        "tourist_info": "Info",
        "hint1_i18n": {"de": "DE hint1"},
    }
    res = admin_client.post("/api/admin/landmarks", json=payload)
    assert res.status_code == 422
    assert "errors" in res.json()


def test_game_available_languages_are_sorted_union(admin_client):
    _login(admin_client)
    lm1 = admin_client.post(
        "/api/admin/landmarks",
        json={
            "key": "lm-de",
            "name": "LM DE",
            "name_i18n": {"de": "DE"},
            "task": "Task",
            "accepted_answers": ["1"],
            "tourist_info": "Info",
        },
    ).json()
    lm2 = admin_client.post(
        "/api/admin/landmarks",
        json={
            "key": "lm-sr",
            "name": "LM SR",
            "task_i18n": {"sr": "SR"},
            "task": "Task",
            "accepted_answers": ["1"],
            "tourist_info": "Info",
        },
    ).json()
    game = admin_client.post(
        "/api/admin/games",
        json={
            "key": "lang-game",
            "name": "Lang Game",
            "intro": "Intro",
            "time_zone": "Europe/Sofia",
            "max_duration_minutes": 60,
        },
    ).json()
    admin_client.put(f"/api/admin/games/{game['id']}/tasks", json={"landmark_ids": [lm1["id"], lm2["id"]]})
    res = admin_client.get(f"/api/admin/games/{game['id']}")
    assert res.status_code == 200
    assert res.json()["available_languages"] == ["de", "sr"]
