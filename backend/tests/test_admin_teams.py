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
from questtour.auth import auth_router
from questtour.db import Base
from questtour.models import Assignment
from questtour.settings import Settings
from questtour.storage import LocalBlobStore
from questtour.tokens import hash_token


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


def _create_game(client: TestClient, *, key: str = "city-tour", name: str = "City Tour") -> int:
    resp = client.post(
        "/api/admin/games",
        json={
            "key": key,
            "name": name,
            "intro": f"Welcome to {name}.",
            "time_zone": "Europe/Sofia",
            "max_duration_minutes": 120,
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def test_team_crud(admin_client, session_factory):
    _login(admin_client)

    # Create
    resp = admin_client.post(
        "/api/admin/teams",
        json={"key": "explorers", "name": "Explorers", "participants": 4},
    )
    assert resp.status_code == 201
    data = resp.json()
    team_id = data["id"]
    assert data["key"] == "explorers"
    assert data["name"] == "Explorers"
    assert data["participants"] == 4
    assert "updated_at" in data

    # List
    resp = admin_client.get("/api/admin/teams")
    assert resp.status_code == 200
    assert resp.json()[0]["key"] == "explorers"

    # Get
    resp = admin_client.get(f"/api/admin/teams/{team_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Explorers"

    # Update
    updated_at = resp.json()["updated_at"]
    resp = admin_client.put(
        f"/api/admin/teams/{team_id}",
        json={"key": "explorers", "name": "Explorers Updated", "participants": 5, "seen_at": updated_at},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Explorers Updated"
    assert resp.json()["participants"] == 5

    # Delete
    resp = admin_client.delete(f"/api/admin/teams/{team_id}")
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True

    resp = admin_client.get(f"/api/admin/teams/{team_id}")
    assert resp.status_code == 404


def test_duplicate_key_and_name_return_field_errors(admin_client):
    _login(admin_client)
    admin_client.post("/api/admin/teams", json={"key": "team-a", "name": "Team A"})

    resp = admin_client.post("/api/admin/teams", json={"key": "team-a", "name": "Other"})
    assert resp.status_code == 422
    errors = resp.json()["errors"]
    assert any(e["field"] == "key" for e in errors)

    resp = admin_client.post("/api/admin/teams", json={"key": "team-b", "name": "Team A"})
    assert resp.status_code == 422
    errors = resp.json()["errors"]
    assert any(e["field"] == "name" for e in errors)


def test_updating_assignments_issues_tokens_only_for_new_and_deactivated(admin_client, session_factory):
    _login(admin_client)
    game_id = _create_game(admin_client)
    team_resp = admin_client.post(
        "/api/admin/teams",
        json={"key": "explorers", "name": "Explorers", "participants": 4},
    )
    team_id = team_resp.json()["id"]
    seen_at = team_resp.json()["updated_at"]

    valid_from = "2026-10-14T09:00:00+03:00"
    valid_until = "2026-10-14T18:00:00+03:00"

    resp = admin_client.put(
        f"/api/admin/teams/{team_id}/assignments",
        json={
            "assignments": [
                {"game_id": game_id, "valid_from": valid_from, "valid_until": valid_until}
            ],
            "seen_at": seen_at,
        },
    )
    assert resp.status_code == 200
    reveals = resp.json()
    assert len(reveals) == 1
    assert reveals[0]["token"]
    assert reveals[0]["url"] == f"http://test/play/{reveals[0]['token']}"

    # Fetch the issued token hash from the DB
    with session_factory() as session:
        assignment = session.scalar(select(Assignment).where(Assignment.team_id == team_id))
        first_hash = assignment.token_hash

    # Updating with the same game but different message/times preserves the token.
    resp = admin_client.put(
        f"/api/admin/teams/{team_id}/assignments",
        json={
            "assignments": [
                {
                    "game_id": game_id,
                    "valid_from": valid_from,
                    "valid_until": valid_until,
                    "exit_message": "See you later",
                }
            ]
        },
    )
    assert resp.status_code == 200
    assert resp.json() == []

    with session_factory() as session:
        assignment = session.scalar(select(Assignment).where(Assignment.team_id == team_id))
        assert assignment.token_hash == first_hash
        assert assignment.exit_message == "See you later"


def test_reissue_changes_token_and_invalidates_old_one(admin_client, session_factory):
    _login(admin_client)
    game_id = _create_game(admin_client)
    team_resp = admin_client.post(
        "/api/admin/teams",
        json={"key": "explorers", "name": "Explorers"},
    )
    team_id = team_resp.json()["id"]

    valid_from = "2026-10-14T09:00:00+03:00"
    valid_until = "2026-10-14T18:00:00+03:00"

    resp = admin_client.put(
        f"/api/admin/teams/{team_id}/assignments",
        json={
            "assignments": [
                {"game_id": game_id, "valid_from": valid_from, "valid_until": valid_until}
            ]
        },
    )
    assignment_id = resp.json()[0]["assignment_id"]
    old_token = resp.json()[0]["token"]

    reissue = admin_client.post(f"/api/admin/assignments/{assignment_id}/reissue", json={})
    assert reissue.status_code == 200
    new_token = reissue.json()["token"]
    assert new_token != old_token

    with session_factory() as session:
        assignment = session.get(Assignment, assignment_id)
        assert assignment.token_hash == hash_token(new_token)
        assert assignment.token_hash != hash_token(old_token)


def test_invalid_timestamp_returns_structured_field_error(admin_client):
    _login(admin_client)
    game_id = _create_game(admin_client)
    team_resp = admin_client.post(
        "/api/admin/teams",
        json={"key": "explorers", "name": "Explorers"},
    )
    team_id = team_resp.json()["id"]

    resp = admin_client.put(
        f"/api/admin/teams/{team_id}/assignments",
        json={
            "assignments": [
                {
                    "game_id": game_id,
                    "valid_from": "not-a-timestamp",
                    "valid_until": "2026-10-14T18:00:00+03:00",
                }
            ]
        },
    )
    assert resp.status_code == 422
    errors = resp.json()["errors"]
    assert any("valid_from" in e["field"] for e in errors)


def test_assignment_valid_until_must_be_after_valid_from(admin_client):
    _login(admin_client)
    game_id = _create_game(admin_client)
    team_resp = admin_client.post(
        "/api/admin/teams",
        json={"key": "explorers", "name": "Explorers"},
    )
    team_id = team_resp.json()["id"]

    resp = admin_client.put(
        f"/api/admin/teams/{team_id}/assignments",
        json={
            "assignments": [
                {
                    "game_id": game_id,
                    "valid_from": "2026-10-14T18:00:00+03:00",
                    "valid_until": "2026-10-14T09:00:00+03:00",
                }
            ]
        },
    )
    assert resp.status_code == 422
    errors = resp.json()["errors"]
    assert any("valid_until" in e["field"] for e in errors)


def test_removing_game_from_assignments_deactivates_it(admin_client, session_factory):
    _login(admin_client)
    game_a = _create_game(admin_client, key="game-a", name="Game A")
    game_b = _create_game(admin_client, key="game-b", name="Game B")
    team_resp = admin_client.post(
        "/api/admin/teams",
        json={"key": "explorers", "name": "Explorers"},
    )
    team_id = team_resp.json()["id"]

    valid_from = "2026-10-14T09:00:00+03:00"
    valid_until = "2026-10-14T18:00:00+03:00"

    resp = admin_client.put(
        f"/api/admin/teams/{team_id}/assignments",
        json={
            "assignments": [
                {"game_id": game_a, "valid_from": valid_from, "valid_until": valid_until},
                {"game_id": game_b, "valid_from": valid_from, "valid_until": valid_until},
            ]
        },
    )
    reveals = resp.json()
    assert len(reveals) == 2

    # Remove game B
    resp = admin_client.put(
        f"/api/admin/teams/{team_id}/assignments",
        json={
            "assignments": [
                {"game_id": game_a, "valid_from": valid_from, "valid_until": valid_until}
            ]
        },
    )
    assert resp.status_code == 200

    with session_factory() as session:
        assignments = session.scalars(select(Assignment).where(Assignment.team_id == team_id)).all()
        by_game = {a.game_id: a for a in assignments}
        assert by_game[game_a].token_hash is not None
        assert by_game[game_b].token_hash is None


def test_delete_team_blocked_when_it_has_assignments(admin_client):
    _login(admin_client)
    game_id = _create_game(admin_client)
    team_resp = admin_client.post(
        "/api/admin/teams",
        json={"key": "explorers", "name": "Explorers"},
    )
    team_id = team_resp.json()["id"]

    admin_client.put(
        f"/api/admin/teams/{team_id}/assignments",
        json={
            "assignments": [
                {
                    "game_id": game_id,
                    "valid_from": "2026-10-14T09:00:00+03:00",
                    "valid_until": "2026-10-14T18:00:00+03:00",
                }
            ]
        },
    )

    resp = admin_client.delete(f"/api/admin/teams/{team_id}")
    assert resp.status_code == 409
    assert resp.json()["detail"] == "cannot delete a team that has assignments"


def test_concurrent_assignment_edits_detected_via_team_updated_at(admin_client):
    _login(admin_client)
    game_id = _create_game(admin_client)
    team_resp = admin_client.post(
        "/api/admin/teams",
        json={"key": "explorers", "name": "Explorers"},
    )
    team_id = team_resp.json()["id"]
    stale_seen_at = "2026-10-01T00:00:00+00:00"

    resp = admin_client.put(
        f"/api/admin/teams/{team_id}/assignments",
        json={
            "assignments": [
                {
                    "game_id": game_id,
                    "valid_from": "2026-10-14T09:00:00+03:00",
                    "valid_until": "2026-10-14T18:00:00+03:00",
                }
            ],
            "seen_at": stale_seen_at,
        },
    )
    assert resp.status_code == 409
    data = resp.json()
    assert data["entity"] == "Team"
    assert data["current"]["id"] == team_id
    assert "updated_at" in data["current"]


def test_update_team_with_stale_seen_at_returns_409(admin_client):
    _login(admin_client)
    team_resp = admin_client.post(
        "/api/admin/teams",
        json={"key": "explorers", "name": "Explorers"},
    )
    team_id = team_resp.json()["id"]

    resp = admin_client.put(
        f"/api/admin/teams/{team_id}",
        json={
            "key": "explorers",
            "name": "Explorers Updated",
            "participants": 5,
            "seen_at": "2026-10-01T00:00:00+00:00",
        },
    )
    assert resp.status_code == 409
    data = resp.json()
    assert data["entity"] == "Team"
    assert data["current"]["id"] == team_id
    assert "updated_at" in data["current"]


def test_list_assignments_for_team(admin_client):
    _login(admin_client)
    game_id = _create_game(admin_client)
    team_resp = admin_client.post(
        "/api/admin/teams",
        json={"key": "explorers", "name": "Explorers"},
    )
    team_id = team_resp.json()["id"]

    admin_client.put(
        f"/api/admin/teams/{team_id}/assignments",
        json={
            "assignments": [
                {
                    "game_id": game_id,
                    "valid_from": "2026-10-14T09:00:00+03:00",
                    "valid_until": "2026-10-14T18:00:00+03:00",
                }
            ]
        },
    )

    resp = admin_client.get(f"/api/admin/assignments/team/{team_id}")
    assert resp.status_code == 200
    assignments = resp.json()
    assert len(assignments) == 1
    assert assignments[0]["game_id"] == game_id
    assert assignments[0]["token_issued"] is True
