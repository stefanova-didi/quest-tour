"""compass support: landmark coordinates, run_task compass_opened_at"""
import sqlalchemy as sa

from alembic import op

revision = "0003"
down_revision = "0002"


def upgrade() -> None:
    op.add_column("landmarks", sa.Column("coordinates_lat", sa.Float(), nullable=True))
    op.add_column("landmarks", sa.Column("coordinates_lon", sa.Float(), nullable=True))
    op.add_column(
        "run_tasks",
        sa.Column("compass_opened_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    with op.batch_alter_table("run_tasks") as batch:
        batch.drop_column("compass_opened_at")
    with op.batch_alter_table("landmarks") as batch:
        batch.drop_column("coordinates_lon")
        batch.drop_column("coordinates_lat")
