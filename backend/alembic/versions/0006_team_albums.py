"""team_albums: the stored memories album PDF of a finished run (issue #33)"""
import sqlalchemy as sa

from alembic import op

revision = "0006"
down_revision = "0005"


def upgrade() -> None:
    op.create_table(
        "team_albums",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("assignment_id", sa.Integer(), sa.ForeignKey("assignments.id"), nullable=False),
        sa.Column("blob_name", sa.String(length=500), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("assignment_id", name="uq_team_albums_assignment"),
        sa.UniqueConstraint("blob_name", name="uq_team_albums_blob_name"),
    )


def downgrade() -> None:
    op.drop_table("team_albums")
