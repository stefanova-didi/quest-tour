import hashlib
from datetime import UTC
from pathlib import Path

import pytest
from sqlalchemy import select

from questtour.cli.sync_config import main
from questtour.db import Base
from questtour.models import Assignment, Game, GameRun, RunTask
from questtour.services.game import start_run
from questtour.settings import get_settings
from questtour.sync.apply import apply_config
from questtour.sync.loader import load_config
from questtour.sync.teams_file import issue_tokens, write_teams_file
from questtour.tokens import hash_token

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
    valid_from: "2026-10-01T00:00:00"
    valid_until: "2026-10-31T23:59:59+02:00"
    exit_message: Bye
"""


def write_config(
    root: Path, *, landmarks: str = LANDMARKS, games: str = GAMES, teams: str = TEAMS
) -> Path:
    (root / "images").mkdir(parents=True, exist_ok=True)
    (root / "images" / "a.svg").write_bytes(SVG)
    for name, text in (("landmarks.yaml", landmarks), ("games.yaml", games), ("teams.yaml", teams)):
        (root / name).write_text(text, encoding="utf-8")
    return root


def sync(root: Path, session_factory, blob_store, reissue=None) -> dict:
    cfg = load_config(root)
    assert cfg.errors == []
    issued = issue_tokens(cfg, reissue)
    if issued:
        write_teams_file(cfg)
    with session_factory() as s:
        apply_config(
            s, blob_store, cfg, host_id="default", images_container="images",
            photos_container="photos",
        )
        s.commit()
    return issued


def test_validation_reports_all_problems(tmp_path):
    write_config(
        tmp_path,
        landmarks="""
landmarks:
  - {id: a, name: A, task: T, accepted_answers: [x], hint2: only-two, tourist_info: I}
  - {id: a, name: B, task: T, accepted_answers: ["!!"], tourist_info: I, task_picture: images/missing.png}
""",
        games="""
games:
  - {id: g, name: G, intro: I, time_zone: Mars/Base, max_duration_minutes: 60, tasks: [a, nope]}
""",
        teams="""
teams: [{id: t, name: T}]
assignments:
  - {team: t, game: g, valid_from: 2026-10-01T00:00:00, valid_until: "2026-10-02T00:00:00"}
""",
    )
    errors = load_config(tmp_path).errors
    text = "\n".join(errors)
    assert "hint2 is set but hint1 is empty" in text
    assert "empty after normalisation" in text
    assert "unknown time zone" in text
    assert "write the timestamp in quotes" in text


def test_cross_check_finds_duplicates_missing_images_and_bad_windows(tmp_path):
    write_config(
        tmp_path,
        landmarks="""
landmarks:
  - {id: a, name: A, task: T, accepted_answers: [x], tourist_info: I}
  - {id: a, name: B, task: T, accepted_answers: [y], tourist_info: I, task_picture: images/missing.png}
""",
        games="""
games:
  - {id: g, name: G, intro: I, time_zone: Europe/Sofia, max_duration_minutes: 60, tasks: [a, nope]}
""",
        teams="""
teams: [{id: t, name: T}, {id: u, name: t}]
assignments:
  - {team: t, game: g, valid_from: "2026-10-02T00:00:00", valid_until: "2026-10-01T00:00:00"}
  - {team: t, game: g, valid_from: "2026-10-01T00:00:00", valid_until: "2026-10-02T00:00:00"}
""",
    )
    text = "\n".join(load_config(tmp_path).errors)
    assert "duplicate landmark id 'a'" in text
    assert "duplicate team name" in text
    assert "picture not found: images/missing.png" in text
    assert "unknown landmark 'nope'" in text
    assert "valid_from must be before valid_until" in text
    assert "duplicate assignment 't/g'" in text


def test_missing_files_are_reported(tmp_path):
    errors = load_config(tmp_path).errors
    for name in ("landmarks", "games", "teams"):
        expected = f"{name}.yaml: file not found (looked in {(tmp_path / f'{name}.yaml').resolve()})"
        assert expected in errors


def test_tokens_written_back_and_comments_kept(tmp_path, session_factory, blob_store):
    write_config(tmp_path)                       # default teams.yaml starts with "# keep this repo private"
    cfg = load_config(tmp_path)
    issued = issue_tokens(cfg)
    write_teams_file(cfg)
    text = (tmp_path / "teams.yaml").read_text(encoding="utf-8")
    token = next(iter(issued.values()))
    assert f"token: {token}" in text and "# keep this repo private" in text
    assert "\n  - team: t\n    game: g\n" in text              # original indentation kept (small diff)
    assert not (tmp_path / "teams.yaml.tmp").exists()
    with session_factory() as s:
        apply_config(
            s, blob_store, cfg, host_id="default", images_container="images",
            photos_container="photos",
        )
        s.commit()
        a = s.scalars(select(Assignment)).one()
        assert a.token_hash == hash_token(token)
        assert a.valid_from.utcoffset() is not None or a.valid_from.tzinfo == UTC


def test_reissue_unknown_assignment_raises(tmp_path):
    write_config(tmp_path)
    cfg = load_config(tmp_path)
    with pytest.raises(ValueError, match="no assignment"):
        issue_tokens(cfg, ("t", "nope"))


def test_reissue_invalidates_old_token(tmp_path, session_factory, blob_store):
    root = write_config(tmp_path)
    old = next(iter(sync(root, session_factory, blob_store).values()))
    new = sync(root, session_factory, blob_store, reissue=("t", "g"))[("t", "g")]
    assert new != old and f"token: {new}" in (root / "teams.yaml").read_text(encoding="utf-8")
    with session_factory() as s:
        assert s.scalars(select(Assignment)).one().token_hash == hash_token(new)


def test_second_sync_is_idempotent_and_keeps_run_snapshot(
    tmp_path, session_factory, blob_store, clock
):
    root = write_config(tmp_path)
    sync(root, session_factory, blob_store)
    with session_factory() as s:
        start_run(s, s.scalars(select(Assignment)).one(), clock.now)
        s.commit()
    assert sync(root, session_factory, blob_store) == {}                    # no new tokens
    write_config(
        tmp_path,
        games=GAMES.replace("tasks: [a, b]", "tasks: [b]"),
        teams=(root / "teams.yaml").read_text(encoding="utf-8"),
    )
    sync(root, session_factory, blob_store)
    with session_factory() as s:
        assert [t.landmark.key for t in s.scalars(select(Game)).one().tasks] == ["b"]
        assert s.query(RunTask).count() == 2                                 # run kept its snapshot
        assert s.query(GameRun).count() == 1


def test_removed_assignment_is_deactivated(tmp_path, session_factory, blob_store):
    root = write_config(tmp_path)
    sync(root, session_factory, blob_store)
    write_config(tmp_path, teams="teams:\n  - {id: t, name: Team T}\nassignments: []\n")
    sync(root, session_factory, blob_store)
    with session_factory() as s:
        assert s.scalars(select(Assignment)).one().token_hash is None


def test_images_uploaded_once_under_content_hash(tmp_path, session_factory, blob_store):
    root = write_config(tmp_path)
    sync(root, session_factory, blob_store)
    sync(root, session_factory, blob_store)
    assert blob_store.get("images", hashlib.sha256(SVG).hexdigest() + ".svg") == (
        SVG,
        "image/svg+xml",
    )


def test_numeric_yaml_values_are_text(tmp_path):
    write_config(
        tmp_path,
        landmarks=LANDMARKS.replace("accepted_answers: [Beta]", "accepted_answers: [1879, Beta]"),
    )
    cfg = load_config(tmp_path)
    assert cfg.errors == [] and cfg.landmarks[1].accepted_answers == ["1879", "Beta"]


def test_cli_validate_only(tmp_path, monkeypatch, capsys):
    write_config(tmp_path)
    monkeypatch.chdir(tmp_path)  # main() calls load_dotenv(".env"): never load backend/.env here
    assert main(["--config-dir", str(tmp_path), "--validate-only"]) == 0
    assert "Configuration is valid." in capsys.readouterr().out


def test_cli_reports_errors_and_changes_nothing(tmp_path, monkeypatch, capsys):
    write_config(tmp_path, games="games: []\n")
    before = (tmp_path / "teams.yaml").read_text(encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert main(["--config-dir", str(tmp_path)]) == 1
    assert "problem(s) found; nothing was changed." in capsys.readouterr().err
    assert (tmp_path / "teams.yaml").read_text(encoding="utf-8") == before


def test_cli_full_run(tmp_path, monkeypatch, capsys):
    from sqlalchemy import create_engine

    root = write_config(tmp_path / "config")
    db = tmp_path / "db.sqlite"
    Base.metadata.create_all(create_engine(f"sqlite:///{db.as_posix()}"))
    monkeypatch.chdir(tmp_path)                      # no stray backend/.env is picked up
    for key, value in {
        "DATABASE_URL": f"sqlite:///{db.as_posix()}",
        "STORAGE_BACKEND": "local",
        "LOCAL_STORAGE_DIR": str(tmp_path / "blobs"),
        "PUBLIC_BASE_URL": "http://test",
    }.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()
    try:
        assert main(["--config-dir", str(root)]) == 0
        assert "http://test/play/" in capsys.readouterr().out
        assert main(["--config-dir", str(root)]) == 0
        assert "(new)" not in capsys.readouterr().out
    finally:
        get_settings.cache_clear()
