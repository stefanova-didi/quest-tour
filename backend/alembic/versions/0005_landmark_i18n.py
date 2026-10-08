"""Add per-landmark i18n JSON columns.

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-07 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("landmarks", sa.Column("name_i18n", sa.JSON(), nullable=True))
    op.add_column("landmarks", sa.Column("task_text_i18n", sa.JSON(), nullable=True))
    op.add_column("landmarks", sa.Column("hint1_i18n", sa.JSON(), nullable=True))
    op.add_column("landmarks", sa.Column("hint2_i18n", sa.JSON(), nullable=True))
    op.add_column("landmarks", sa.Column("info_text_i18n", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("landmarks", "info_text_i18n")
    op.drop_column("landmarks", "hint2_i18n")
    op.drop_column("landmarks", "hint1_i18n")
    op.drop_column("landmarks", "task_text_i18n")
    op.drop_column("landmarks", "name_i18n")
