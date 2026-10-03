from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from questtour.api.schemas import LeaderboardRowOut
from questtour.models import Assignment, GameRun
from questtour.services.game import hints_used, total_seconds


@dataclass(frozen=True)
class Entry:
    run_id: int
    team_name: str
    total_seconds: int
    hints_used: int


def rank_entries(entries: list[Entry], viewer_run_id: int | None) -> list[LeaderboardRowOut]:
    """R-12: lowest total first; equal seconds share a rank (1, 2, 2, 4)."""
    ordered = sorted(entries, key=lambda e: (e.total_seconds, e.team_name.casefold()))
    rows: list[LeaderboardRowOut] = []
    rank, previous = 0, None
    for index, entry in enumerate(ordered, start=1):
        if entry.total_seconds != previous:
            rank, previous = index, entry.total_seconds
        rows.append(
            LeaderboardRowOut(
                rank=rank,
                team_name=entry.team_name,
                total_seconds=entry.total_seconds,
                hints_used=entry.hints_used,
                is_you=entry.run_id == viewer_run_id,
            )
        )
    return rows


def leaderboard_rows(
    session: Session, game_id: int, viewer_run_id: int | None
) -> list[LeaderboardRowOut]:
    runs = session.scalars(
        select(GameRun)
        .join(GameRun.assignment)
        .where(Assignment.game_id == game_id, GameRun.end_reason == "finished")
        .options(
            selectinload(GameRun.tasks),
            selectinload(GameRun.assignment).selectinload(Assignment.team),
        )
    ).all()
    return rank_entries(
        [Entry(r.id, r.assignment.team.name, total_seconds(r), hints_used(r)) for r in runs],
        viewer_run_id,
    )
