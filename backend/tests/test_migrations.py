import io
import logging
from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

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


def test_photo_deleted_at_is_nullable_and_indexed(tmp_path):
    url = f"sqlite:///{tmp_path / 'm.db'}"
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    engine = create_engine(url)
    inspector = inspect(engine)
    columns = {c["name"]: c for c in inspector.get_columns("photos")}
    assert columns["deleted_at"]["nullable"] is True
    indexes = {idx["name"] for idx in inspector.get_indexes("photos")}
    assert "ix_photos_deleted_at" in indexes


def test_sqlite_upgrade_emits_no_native_alter_column(tmp_path):
    """SQLite cannot run ``ALTER TABLE ... ALTER COLUMN ... SET NOT NULL`` (only added in
    SQLite >= 3.53; ubuntu-latest runners ship an older sqlite3). Migrations must use the
    batch table-rebuild strategy instead, which every supported SQLite version can run."""
    url = f"sqlite:///{tmp_path / 'p.db'}"
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger = logging.getLogger("sqlalchemy.engine")
    previous_level = logger.level
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    try:
        command.upgrade(cfg, "head")
    finally:
        handler.close()
        logger.removeHandler(handler)
        logger.setLevel(previous_level)

    ddl = stream.getvalue()
    assert "ALTER COLUMN" not in ddl
    assert "_alembic_tmp" in ddl  # batch table-rebuild actually ran, not a silent no-op
