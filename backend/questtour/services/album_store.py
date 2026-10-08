"""Stored album PDFs (issue #33): generated once per finished run, kept in the ``albums`` blob
container for the host, handed to the team on request, and removable by the host from the admin
panel – after which the team's link answers 410 and nothing is regenerated unless the host asks.
"""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from questtour.models import Assignment, GameRun, TeamAlbum
from questtour.safenames import safe_name
from questtour.services.album import build_album, run_photos
from questtour.services.album_pdf import render_album_pdf
from questtour.settings import Settings
from questtour.storage import BlobStore

log = logging.getLogger("questtour.album")
PDF = "application/pdf"


def album_blob_name(game_name: str, team_name: str, started_local: datetime) -> str:
    return f"{safe_name(game_name)}/{safe_name(team_name)}/{started_local:%Y-%m-%d}_memories-album.pdf"


def album_file_name(team_name: str) -> str:
    return f"{safe_name(team_name)}-memories-album.pdf"


def get_album_record(session: Session, assignment_id: int) -> TeamAlbum | None:
    return session.scalar(select(TeamAlbum).where(TeamAlbum.assignment_id == assignment_id))


def generate_album(
    session: Session,
    store: BlobStore,
    settings: Settings,
    assignment: Assignment,
    run: GameRun,
    now: datetime,
) -> TeamAlbum:
    """Render the album from the run's current photos and stories and store it, replacing any
    earlier file (the host may regenerate after deleting a photo, or after removing the album)."""
    album = build_album(session, assignment, run, "", now)
    images: dict[int, bytes] = {}
    for photos in run_photos(session, run).values():
        for photo in photos:
            found = store.get(settings.photos_container, photo.blob_name)
            if found is not None:
                images[photo.id] = found[0]
    data = render_album_pdf(album, images)
    started_local = run.started_at.astimezone(ZoneInfo(assignment.game.time_zone))
    name = album_blob_name(assignment.game.name, assignment.team.name, started_local)
    store.put(settings.albums_container, name, data, PDF, overwrite=True)
    record = get_album_record(session, assignment.id)
    if record is None:
        record = TeamAlbum(assignment_id=assignment.id, blob_name=name)
        session.add(record)
    elif record.blob_name != name:
        store.delete(settings.albums_container, record.blob_name)
        record.blob_name = name
    record.size_bytes = len(data)
    record.generated_at = now
    record.deleted_at = None
    session.flush()
    log.info("album generated assignment=%s bytes=%s", assignment.id, len(data))
    return record


def ensure_album(
    session: Session,
    store: BlobStore,
    settings: Settings,
    assignment: Assignment,
    run: GameRun,
    now: datetime,
) -> TeamAlbum | None:
    """The stored album, generated on first request; None once the host has removed it."""
    record = get_album_record(session, assignment.id)
    if record is not None:
        return None if record.deleted_at is not None else record
    return generate_album(session, store, settings, assignment, run, now)


def delete_album(store: BlobStore, settings: Settings, record: TeamAlbum, now: datetime) -> None:
    """Host action: drop the file and remember that it was removed (players get 410)."""
    store.delete(settings.albums_container, record.blob_name)
    record.deleted_at = now


def invalidate_album(session: Session, store: BlobStore, settings: Settings, assignment_id: int) -> None:
    """A photo was deleted: a stored album would now be stale, so drop it; the next request renders
    it afresh. An album the host removed stays removed."""
    record = get_album_record(session, assignment_id)
    if record is None or record.deleted_at is not None:
        return
    store.delete(settings.albums_container, record.blob_name)
    session.delete(record)
