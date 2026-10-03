from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine

from alembic import command
from questtour import models  # noqa: F401
from questtour.db import Base

BACKEND = Path(__file__).resolve().parents[1]


def test_migration_matches_models(tmp_path):
    url = f"sqlite:///{tmp_path / 'm.db'}"
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    with create_engine(url).connect() as conn:
        ctx = MigrationContext.configure(conn, opts={"compare_type": False})
        diffs = [d for d in compare_metadata(ctx, Base.metadata)]
    assert diffs == []
