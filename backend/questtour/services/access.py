from datetime import datetime
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from questtour.models import Assignment, Game, GameRun, GameTask
from questtour.services.game import is_service
from questtour.tokens import hash_token

Reason = Literal["unknown", "not_yet", "expired"]


class LinkNotValid(Exception):
    def __init__(
        self,
        reason: Reason,
        *,
        opens_at: datetime | None = None,
        expired_at: datetime | None = None,
        time_zone: str | None = None,
    ) -> None:
        super().__init__(reason)
        self.reason = reason
        self.opens_at = opens_at
        self.expired_at = expired_at
        self.time_zone = time_zone


def find_assignment(session: Session, token: str, *, lock: bool = False) -> Assignment:
    stmt = (
        select(Assignment)
        .where(Assignment.token_hash == hash_token(token))
        .options(
            selectinload(Assignment.team),
            selectinload(Assignment.game).selectinload(Game.tasks).selectinload(GameTask.landmark),
        )
    )
    if lock:
        stmt = stmt.with_for_update()
    assignment = session.scalars(stmt).one_or_none()
    if assignment is None:  # unknown, reissued or deactivated token
        raise LinkNotValid("unknown")
    return assignment


def ensure_link_usable(assignment: Assignment, run: GameRun | None, now: datetime) -> None:
    """Validity window gates only assignments that never started (clarification: post-window access).
    A started run always resolves to its current or final state; time limits end it
    (game.apply_time_limits). Service links (R-25) are never gated."""
    if run is not None or is_service(assignment):
        return
    tz = assignment.game.time_zone
    if now < assignment.valid_from:
        raise LinkNotValid("not_yet", opens_at=assignment.valid_from, time_zone=tz)
    if now >= assignment.valid_until:
        raise LinkNotValid("expired", expired_at=assignment.valid_until, time_zone=tz)
