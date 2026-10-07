from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from questtour.cli.sync_config import main
from questtour.main import _acquire_seed_lock
from questtour.models import Assignment, Game, Landmark, Team
from questtour.settings import Settings

SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"/>'

LANDMARKS = """
landmarks:
  - {id: a, name: Alpha, task: Riddle A, accepted_answers: [Alpha], tourist_info: Info A,
     task_picture: images/a.svg}
  - {id: b, name: Beta, task: Riddle B, accepted_answers: [Beta], tourist_info: Info B}
"""

GAMES = """
games:
  - {id: g, name: Game G, intro: Hi, time_zone: Europe/Sofia, max_duration_minutes: 240, tasks: [a, b]}
"""

TEAMS = """# keep this repo private
teams:
  - {id: t, name: Team T}
assignments:
  - team: t
    game: g
    valid_from: "2026-10-01T00:00:00+03:00"
    valid_until: "2026-10-31T23:59:59+03:00"
    exit_message: Bye
"""


def write_config(root: Path) -> Path:
    (root / "images").mkdir(parents=True, exist_ok=True)
    (root / "images" / "a.svg").write_bytes(SVG)
    for name, text in (
        ("landmarks.yaml", LANDMARKS),
        ("games.yaml", GAMES),
        ("teams.yaml", TEAMS),
    ):
        (root / name).write_text(text, encoding="utf-8")
    return root


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    return write_config(tmp_path / "config")


@pytest.fixture
def seeded_settings(settings, config_dir: Path) -> Settings:
    return settings.model_copy(update={"config_dir": config_dir})


@pytest.fixture
def seeded_app(seeded_settings, session_factory, blob_store, clock):
    from questtour.main import create_app

    return create_app(
        seeded_settings,
        session_factory=session_factory,
        blob_store=blob_store,
        clock=clock,
    )


@pytest.fixture
def seeded_client(seeded_app):
    with TestClient(seeded_app, headers={"X-Device-Id": "device-aaaa-0001"}) as client:
        yield client


def test_auto_imports_valid_yaml_when_db_is_empty(seeded_client, session_factory):
    resp = seeded_client.get("/api/health")
    assert resp.status_code == 200

    with session_factory() as s:
        assert s.scalar(select(Landmark).where(Landmark.key == "a")) is not None
        assert s.scalar(select(Game).where(Game.key == "g")) is not None
        assert s.scalar(select(Team).where(Team.key == "t")) is not None
        assignment = s.scalar(select(Assignment))
        assert assignment is not None
        assert assignment.token_hash is not None
        assert assignment.issued_at is not None


def test_auto_import_skips_when_db_is_populated(seeded_settings, session_factory, blob_store, clock):
    from questtour.main import create_app

    # Pre-populate the database with a landmark so the seed import is skipped.
    with session_factory() as s:
        s.add(
            Landmark(
                host_id=seeded_settings.host_id,
                key="existing",
                name="Existing Landmark",
                task_text="Task",
                accepted_answers=["answer"],
                info_text="Info",
            )
        )
        s.commit()

    app = create_app(
        seeded_settings,
        session_factory=session_factory,
        blob_store=blob_store,
        clock=clock,
    )
    with TestClient(app, headers={"X-Device-Id": "device-aaaa-0001"}) as client:
        assert client.get("/api/health").status_code == 200

    with session_factory() as s:
        assert s.scalar(select(Landmark).where(Landmark.key == "a")) is None
        assert s.scalar(select(Landmark).where(Landmark.key == "existing")) is not None
        assert s.scalar(select(Team).where(Team.key == "t")) is None


def test_invalid_yaml_sets_seed_error_and_keeps_player_api_up(
    settings, session_factory, blob_store, clock, tmp_path: Path
):
    from questtour.main import create_app

    bad_config = write_config(tmp_path / "bad-config")
    (bad_config / "teams.yaml").write_text(
        "teams: [{id: t, name: Team T}]\n"
        "assignments:\n"
        "  - {team: t, game: missing-game, valid_from: \"2026-10-01T00:00:00+03:00\", valid_until: \"2026-10-02T00:00:00+03:00\"}\n",
        encoding="utf-8",
    )
    settings = settings.model_copy(update={"config_dir": bad_config})
    app = create_app(settings, session_factory=session_factory, blob_store=blob_store, clock=clock)

    with TestClient(app, headers={"X-Device-Id": "device-aaaa-0002"}) as client:
        assert client.get("/api/health").status_code == 200
    assert app.state.seed_error is not None
    assert "missing-game" in app.state.seed_error


def test_cli_writes_tokens_back_to_teams_yaml(config_dir: Path, monkeypatch, capsys, tmp_path: Path):
    from sqlalchemy import create_engine

    from questtour.db import Base
    from questtour.settings import get_settings

    db = tmp_path / "db.sqlite"
    Base.metadata.create_all(create_engine(f"sqlite:///{db.as_posix()}"))

    monkeypatch.chdir(config_dir.parent)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db.as_posix()}")
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://test")
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("LOCAL_STORAGE_DIR", str(tmp_path / "blobs"))
    get_settings.cache_clear()
    try:
        assert main(["--config-dir", str(config_dir)]) == 0
    finally:
        get_settings.cache_clear()
    text = (config_dir / "teams.yaml").read_text(encoding="utf-8")
    assert "token:" in text
    assert "# keep this repo private" in text
    out = capsys.readouterr().out
    assert "Game links:" in out
    assert "http://test/play/" in out


def test_seed_lock_uses_transaction_scoped_advisory_lock(settings):
    """The startup seed lock must be transaction-scoped so pooled connections do not leak it."""
    import hashlib

    from sqlalchemy.dialects.postgresql import dialect as pg_dialect

    statements = []

    class FakeDialect:
        name = "postgresql"

    class FakeBind:
        dialect = FakeDialect()

    class FakeSession:
        bind = FakeBind()

        def execute(self, stmt):
            statements.append(stmt)

    _acquire_seed_lock(FakeSession(), settings)  # type: ignore[arg-type]

    assert statements, "advisory lock statement should execute"
    compiled = statements[0].compile(dialect=pg_dialect(), compile_kwargs={"literal_binds": True})
    sql = str(compiled)
    assert "pg_advisory_xact_lock" in sql
    assert "pg_advisory_lock(" not in sql

    expected = (
        int(hashlib.sha256(f"{settings.host_id}:questtour_seed".encode()).hexdigest()[:16], 16)
        & 0x7FFFFFFFFFFFFFFF
    )
    assert f"{expected}" in sql


def test_seed_error_endpoint_surfaces_last_error(
    settings, session_factory, blob_store, clock, tmp_path: Path
):
    from questtour.main import create_app

    bad_config = write_config(tmp_path / "bad-config")
    (bad_config / "teams.yaml").write_text(
        "teams: [{id: t, name: Team T}]\n"
        "assignments:\n"
        "  - {team: t, game: missing-game, valid_from: \"2026-10-01T00:00:00+03:00\", valid_until: \"2026-10-02T00:00:00+03:00\"}\n",
        encoding="utf-8",
    )
    settings = settings.model_copy(
        update={"config_dir": bad_config, "admin_dev_emails": ["admin@example.com"]}
    )
    app = create_app(settings, session_factory=session_factory, blob_store=blob_store, clock=clock)

    with TestClient(app, headers={"X-Device-Id": "device-aaaa-0003"}) as client:
        resp = client.post("/api/admin/auth/magic/request", json={"email": "admin@example.com"})
        assert resp.status_code == 200
        url = resp.json()["url"]

        from urllib.parse import parse_qs, urlparse

        params = parse_qs(urlparse(url).query)
        client.get(
            "/api/admin/auth/magic/verify",
            params={"token": params["token"][0], "email": params["email"][0]},
            follow_redirects=False,
        )

        resp = client.get("/api/admin/seed-error")
        assert resp.status_code == 200
        assert resp.json()["error"] is not None
        assert "missing-game" in resp.json()["error"]
