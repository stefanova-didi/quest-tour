import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv  # python-dotenv ships with pydantic-settings
from sqlalchemy.orm import Session

from questtour.db import make_engine
from questtour.settings import get_settings
from questtour.storage import make_blob_store
from questtour.sync.apply import apply_config
from questtour.sync.loader import load_config
from questtour.sync.teams_file import issue_tokens, write_teams_file


def main(argv: list[str] | None = None) -> int:
    load_dotenv(".env")  # so CONFIG_DIR from backend/.env applies; real env vars still win
    parser = argparse.ArgumentParser(
        prog="sync-config", description="Validate and load the config files into the database."
    )
    parser.add_argument(
        "--config-dir", type=Path, default=Path(os.environ.get("CONFIG_DIR", "config"))
    )
    parser.add_argument("--validate-only", action="store_true", help="only validate the YAML files")
    parser.add_argument(
        "--reissue",
        nargs=2,
        metavar=("TEAM_ID", "GAME_ID"),
        help="replace the token of one assignment; the old link stops working",
    )
    args = parser.parse_args(argv)

    cfg = load_config(args.config_dir)
    if cfg.errors:
        for error in cfg.errors:
            print(f"error: {error}", file=sys.stderr)
        print(f"{len(cfg.errors)} problem(s) found; nothing was changed.", file=sys.stderr)
        return 1
    if args.validate_only:
        print("Configuration is valid.")
        return 0

    try:
        issued = issue_tokens(cfg, tuple(args.reissue) if args.reissue else None)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if issued:
        write_teams_file(cfg)  # D13: YAML first, so a failed DB commit can't lose a token
        print(f"Wrote {len(issued)} new token(s) to teams.yaml — commit it (the repo must stay private).")

    settings = get_settings()
    engine = make_engine(settings)
    try:
        with Session(engine) as session:
            report = apply_config(
                session,
                make_blob_store(settings),
                cfg,
                host_id=settings.host_id,
                images_container=settings.images_container,
                photos_container=settings.photos_container,
            )
            session.commit()
    finally:
        engine.dispose()  # release pooled connections (SQLite file lock on Windows)

    print(
        f"Synced {report.landmarks} landmarks, {report.games} games, {report.teams} teams, "
        f"{report.assignments} assignments; uploaded {report.images_uploaded} picture(s)."
    )
    for item in report.deactivated:
        print(f"Deactivated assignment no longer in teams.yaml: {item}")
    for item in report.not_in_config:
        print(f"Left in database (not in config): {item}")
    names = {t.id: t.name for t in cfg.teams}
    games = {g.id: g.name for g in cfg.games}
    print("\nGame links:")
    for a in cfg.assignments:
        mark = " (new)" if (a.team, a.game) in issued else ""
        link = f"{settings.public_base_url.rstrip('/')}/play/{a.token}{mark}"
        print(f"  {names[a.team]} — {games[a.game]}: {link}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
