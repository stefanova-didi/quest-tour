from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from questtour.imagetypes import ImageKind
from questtour.models import Assignment, GameRun, Photo
from questtour.safenames import photo_blob_name
from questtour.services.game import TIMED_OUT, Outcome, bump
from questtour.storage import BlobExists, BlobStore


def save_photo(
    session: Session,
    store: BlobStore,
    container: str,
    run: GameRun,
    assignment: Assignment,
    position: int,
    data: bytes,
    kind: ImageKind,
    now: datetime,
    device_id: str | None,
) -> Outcome:
    """R-10: allowed for any task the team has completed (current or earlier); many photos per landmark;
    original bytes kept. A photo whose upload was still in flight when a teammate pressed Next riddle is
    therefore stored against its own landmark instead of being thrown away."""
    if run.end_reason in TIMED_OUT:
        return Outcome.GAME_OVER
    if not 0 <= position <= min(run.current_position, len(run.tasks) - 1):
        return Outcome.STALE                              # a task the team hasn't reached
    task = run.tasks[position]
    if task.completed_at is None:
        return Outcome.STALE
    game, team = assignment.game, assignment.team
    uploaded_local = now.astimezone(ZoneInfo(game.time_zone))
    suffix = 1
    while True:
        name = photo_blob_name(
            game.name, team.name, uploaded_local, task.position + 1, task.landmark.name, kind.ext, suffix
        )
        try:
            store.put(container, name, data, kind.content_type, overwrite=False)
            break
        except BlobExists:
            suffix += 1                                   # _2, _3, … on name clashes
    session.add(
        Photo(
            run_task_id=task.id,
            device_id=device_id,
            uploaded_at=now,
            blob_name=name,
            content_type=kind.content_type,
            size_bytes=len(data),
        )
    )
    task.photo_count += 1
    bump(run)
    return Outcome.OK
