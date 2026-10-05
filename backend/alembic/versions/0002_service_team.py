"""service (test) team: teams.is_service, assignments.version_floor (R-25)"""
import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"


def upgrade() -> None:
    op.add_column(
        "teams",
        sa.Column("is_service", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "assignments",
        sa.Column("version_floor", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    with op.batch_alter_table("assignments") as batch:
        batch.drop_column("version_floor")
    with op.batch_alter_table("teams") as batch:
        batch.drop_column("is_service")
