"""initial schema"""
import sqlalchemy as sa

from alembic import op

revision = "0001"
down_revision = None
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "landmarks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("host_id", sa.String(64), nullable=False),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("task_text", sa.Text(), nullable=False),
        sa.Column("task_image", sa.String(200)),
        sa.Column("accepted_answers", sa.JSON(), nullable=False),
        sa.Column("hint1", sa.Text()),
        sa.Column("hint2", sa.Text()),
        sa.Column("info_text", sa.Text(), nullable=False),
        sa.Column("info_image", sa.String(200)),
        sa.UniqueConstraint("host_id", "key", name="uq_landmarks_host_key"),
    )
    op.create_table(
        "games",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("host_id", sa.String(64), nullable=False),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("intro", sa.Text(), nullable=False),
        sa.Column("time_zone", sa.String(64), nullable=False),
        sa.Column("max_duration_minutes", sa.Integer(), nullable=False),
        sa.Column("reveal_after_attempts", sa.Integer(), nullable=False),
        sa.Column("reveal_after_minutes", sa.Integer(), nullable=False),
        sa.Column("reveal_penalty_minutes", sa.Integer(), nullable=False),
        sa.UniqueConstraint("host_id", "key", name="uq_games_host_key"),
    )
    op.create_table(
        "game_tasks",
        sa.Column(
            "game_id", sa.Integer(), sa.ForeignKey("games.id", ondelete="CASCADE"), primary_key=True
        ),
        sa.Column("position", sa.Integer(), primary_key=True),
        sa.Column("landmark_id", sa.Integer(), sa.ForeignKey("landmarks.id"), nullable=False),
    )
    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("host_id", sa.String(64), nullable=False),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("participants", sa.Integer()),
        sa.UniqueConstraint("host_id", "key", name="uq_teams_host_key"),
        sa.UniqueConstraint("host_id", "name", name="uq_teams_host_name"),
    )
    op.create_table(
        "assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("host_id", sa.String(64), nullable=False),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("game_id", sa.Integer(), sa.ForeignKey("games.id"), nullable=False),
        sa.Column("token_hash", sa.String(64), unique=True),
        sa.Column("valid_from", TS, nullable=False),
        sa.Column("valid_until", TS, nullable=False),
        sa.Column("exit_message", sa.Text(), nullable=False),
        sa.UniqueConstraint("team_id", "game_id", name="uq_assignments_team_game"),
    )
    op.create_table(
        "game_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "assignment_id",
            sa.Integer(),
            sa.ForeignKey("assignments.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("started_at", TS, nullable=False),
        sa.Column("finished_at", TS),
        sa.Column("ended_at", TS),
        sa.Column("end_reason", sa.String(20)),
        sa.Column("current_position", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    )
    op.create_table(
        "run_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "run_id",
            sa.Integer(),
            sa.ForeignKey("game_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("landmark_id", sa.Integer(), sa.ForeignKey("landmarks.id"), nullable=False),
        sa.Column("shown_at", TS),
        sa.Column("completed_at", TS),
        sa.Column("completion", sa.String(10)),
        sa.Column("hint1_at", TS),
        sa.Column("hint2_at", TS),
        sa.Column("revealed_at", TS),
        sa.Column("hint_penalty_minutes", sa.Integer(), nullable=False),
        sa.Column("reveal_penalty_minutes", sa.Integer(), nullable=False),
        sa.Column("wrong_attempts", sa.Integer(), nullable=False),
        sa.Column("photo_count", sa.Integer(), nullable=False),
        sa.UniqueConstraint("run_id", "position", name="uq_run_tasks_run_position"),
    )
    op.create_table(
        "answer_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "run_task_id",
            sa.Integer(),
            sa.ForeignKey("run_tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("device_id", sa.String(64)),
        sa.Column("submitted_at", TS, nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("correct", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "photos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "run_task_id",
            sa.Integer(),
            sa.ForeignKey("run_tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("device_id", sa.String(64)),
        sa.Column("uploaded_at", TS, nullable=False),
        sa.Column("blob_name", sa.String(500), nullable=False, unique=True),
        sa.Column("content_type", sa.String(50), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
    )
    op.create_table(
        "run_devices",
        sa.Column(
            "run_id",
            sa.Integer(),
            sa.ForeignKey("game_runs.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("device_id", sa.String(64), primary_key=True),
        sa.Column("first_seen_at", TS, nullable=False),
        sa.Column("last_seen_at", TS, nullable=False),
    )


def downgrade() -> None:
    for table in (
        "run_devices",
        "photos",
        "answer_attempts",
        "run_tasks",
        "game_runs",
        "assignments",
        "teams",
        "game_tasks",
        "games",
        "landmarks",
    ):
        op.drop_table(table)
