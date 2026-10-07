import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv  # python-dotenv ships with pydantic-settings
from sqlalchemy.orm import Session

from questtour.db import make_engine
from questtour.services.seed import import_yaml
from questtour.settings import get_settings
from questtour.storage import make_blob_store
from questtour.sync.loader import load_config


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
        help=(
            "replace the token of one assignment (or of the service team's link for a game); "
            "the old link stops working"
        ),
    )
    args = parser.parse_args(argv)

    # Validation can be done without touching the database or requiring full settings.
    cfg = load_config(args.config_dir)
    if cfg.errors:
        for error in cfg.errors:
            print(f"error: {error}", file=sys.stderr)
        print(f"{len(cfg.errors)} problem(s) found; nothing was changed.", file=sys.stderr)
        return 1

    if args.validate_only:
        print("Configuration is valid.")
        return 0

    settings = get_settings()
    if args.config_dir:
        settings = settings.model_copy(update={"config_dir": args.config_dir})

    engine = make_engine(settings)
    try:
        with Session(engine) as session:
            report = import_yaml(
                session=session,
                store=make_blob_store(settings),
                settings=settings,
                write_back=True,
                reissue=tuple(args.reissue) if args.reissue else None,
            )
            if isinstance(report, list):
                for error in report:
                    print(f"error: {error}", file=sys.stderr)
                print(f"{len(report)} problem(s) found; nothing was changed.", file=sys.stderr)
                return 1
            session.commit()
    finally:
        engine.dispose()  # release pooled connections (SQLite file lock on Windows)

    # Reload the round-trip config so link output uses the token values just written to teams.yaml.
    cfg = load_config(settings.config_dir)
    names = {t.id: t.name for t in cfg.teams}
    games = {g.id: g.name for g in cfg.games}
    print(
        f"Synced {report.landmarks} landmarks, {report.games} games, {report.teams} teams, "
        f"{report.assignments} assignments, {report.service_assignments} service link(s); uploaded {report.images_uploaded} picture(s)."
    )
    for item in report.deactivated:
        print(f"Deactivated assignment no longer in teams.yaml: {item}")
    for item in report.not_in_config:
        print(f"Left in database (not in config): {item}")
    print("\nGame links:")
    for a in cfg.assignments:
        mark = " (new)" if (a.team, a.game) in report.issued else ""
        link = f"{settings.public_base_url.rstrip('/')}/play/{a.token}{mark}"
        print(f"  {names[a.team]} — {games[a.game]}: {link}")
    if cfg.service is not None:
        print("\nService (test) links — no time limits, resettable, never on a leaderboard:")
        for g in cfg.games:
            mark = " (new)" if (cfg.service.team, g.id) in report.issued else ""
            link = f"{settings.public_base_url.rstrip('/')}/play/{cfg.service.tokens[g.id]}{mark}"
            print(f"  {cfg.service.name} — {g.name}: {link}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
