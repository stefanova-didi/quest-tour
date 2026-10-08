"""admin panel columns

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-07 00:27:55.044029
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from questtour.db import UTCDateTime

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _backfill(table_name: str) -> None:
    tbl = sa.table(table_name, sa.Column("updated_at", UTCDateTime()))
    op.execute(tbl.update().values(updated_at=sa.func.now()))


def _add_updated_at_not_null(table_name: str) -> None:
    """Add a NOT NULL updated_at: batch mode so SQLite rebuilds the table instead of
    emitting ``ALTER TABLE ... ALTER COLUMN ... SET NOT NULL`` (not supported by the
    sqlite3 shipped on older runners). On PostgreSQL the batch ops run natively."""
    with op.batch_alter_table(table_name) as batch:
        batch.add_column(sa.Column("updated_at", UTCDateTime(), nullable=True))
    _backfill(table_name)
    with op.batch_alter_table(table_name) as batch:
        batch.alter_column("updated_at", existing_type=UTCDateTime(), nullable=False)


def upgrade() -> None:
    _add_updated_at_not_null("landmarks")
    _add_updated_at_not_null("games")
    _add_updated_at_not_null("teams")
    _add_updated_at_not_null("assignments")
    op.add_column(
        "assignments",
        sa.Column("issued_at", UTCDateTime(), nullable=True),
    )

    _add_updated_at_not_null("photos")
    op.add_column(
        "photos",
        sa.Column("deleted_at", UTCDateTime(), nullable=True),
    )
    op.create_index("ix_photos_deleted_at", "photos", ["deleted_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_photos_deleted_at", table_name="photos")
    op.drop_column("photos", "deleted_at")
    op.drop_column("photos", "updated_at")
    op.drop_column("assignments", "issued_at")
    op.drop_column("assignments", "updated_at")
    op.drop_column("teams", "updated_at")
    op.drop_column("games", "updated_at")
    op.drop_column("landmarks", "updated_at")
