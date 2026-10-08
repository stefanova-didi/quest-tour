"""Admin: the stored memories albums (issue #33) – list, generate, download, delete."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import func, select

from questtour.admin.crud import get_admin_host_id
from questtour.api.deps import NowDep, SessionDep
from questtour.auth import AdminSession, require_admin
from questtour.models import Assignment, Game, GameRun, Photo, RunTask, Team, TeamAlbum
from questtour.services.album_store import (
    PDF,
    album_file_name,
    delete_album,
    generate_album,
)
from questtour.storage import StorageUnavailable

router = APIRouter(prefix="/albums", tags=["admin-albums"])


class AlbumFileOut(BaseModel):
    id: int
    size_bytes: int
    generated_at: datetime
    deleted_at: datetime | None
    url: str


class AlbumRowOut(BaseModel):
    """A run that has ended, with its album if one was generated."""

    assignment_id: int
    team_name: str
    game_name: str
    ended_at: datetime
    end_reason: str
    photo_count: int
    album: AlbumFileOut | None


def _download_url(settings, album_id: int) -> str:
    return f"{settings.public_base_url.rstrip('/')}/api/admin/albums/{album_id}/download"


def _file_out(settings, record: TeamAlbum) -> AlbumFileOut:
    return AlbumFileOut(
        id=record.id,
        size_bytes=record.size_bytes,
        generated_at=record.generated_at,
        deleted_at=record.deleted_at,
        url=_download_url(settings, record.id),
    )


def _ended_assignment(session: SessionDep, assignment_id: int, host_id: str) -> tuple[Assignment, GameRun]:
    assignment = session.get(Assignment, assignment_id)
    if assignment is None or assignment.host_id != host_id:
        raise HTTPException(404)
    run = session.scalar(select(GameRun).where(GameRun.assignment_id == assignment.id))
    if run is None or run.end_reason is None:
        raise HTTPException(409, "run_not_ended")
    return assignment, run


@router.get("", response_model=list[AlbumRowOut])
def list_albums(
    request: Request,
    session: SessionDep,
    admin: Annotated[AdminSession, Depends(require_admin)],
    host_id: str = Depends(get_admin_host_id),
):
    photo_counts = (
        select(RunTask.run_id, func.count(Photo.id).label("n"))
        .join(Photo, Photo.run_task_id == RunTask.id)
        .where(Photo.deleted_at.is_(None))
        .group_by(RunTask.run_id)
        .subquery()
    )
    rows = session.execute(
        select(Assignment, GameRun, Team.name, Game.name, TeamAlbum, photo_counts.c.n)
        .join(GameRun, GameRun.assignment_id == Assignment.id)
        .join(Team, Assignment.team_id == Team.id)
        .join(Game, Assignment.game_id == Game.id)
        .outerjoin(TeamAlbum, TeamAlbum.assignment_id == Assignment.id)
        .outerjoin(photo_counts, photo_counts.c.run_id == GameRun.id)
        .where(Assignment.host_id == host_id, GameRun.end_reason.is_not(None))
        .order_by(GameRun.ended_at.desc())
    ).all()
    settings = request.app.state.settings
    return [
        AlbumRowOut(
            assignment_id=assignment.id,
            team_name=team_name,
            game_name=game_name,
            ended_at=run.ended_at,
            end_reason=run.end_reason,
            photo_count=n or 0,
            album=_file_out(settings, record) if record is not None else None,
        )
        for assignment, run, team_name, game_name, record, n in rows
    ]


@router.post("/{assignment_id}/generate", response_model=AlbumFileOut)
def generate(
    assignment_id: int,
    request: Request,
    session: SessionDep,
    now: NowDep,
    admin: Annotated[AdminSession, Depends(require_admin)],
    host_id: str = Depends(get_admin_host_id),
):
    """Render (again) from the run's current photos; also brings back an album the host removed."""
    assignment, run = _ended_assignment(session, assignment_id, host_id)
    settings = request.app.state.settings
    try:
        record = generate_album(session, request.app.state.blob_store, settings, assignment, run, now)
    except StorageUnavailable as exc:
        session.rollback()
        raise HTTPException(503, "Storage unavailable, please retry") from exc
    session.commit()
    return _file_out(settings, record)


def _own_album(session: SessionDep, album_id: int, host_id: str) -> TeamAlbum:
    record = session.get(TeamAlbum, album_id)
    if record is None or record.assignment.host_id != host_id:
        raise HTTPException(404)
    return record


@router.get("/{album_id}/download")
def download(
    album_id: int,
    request: Request,
    session: SessionDep,
    admin: Annotated[AdminSession, Depends(require_admin)],
    host_id: str = Depends(get_admin_host_id),
):
    record = _own_album(session, album_id, host_id)
    if record.deleted_at is not None:
        raise HTTPException(410, "album_removed")
    settings = request.app.state.settings
    found = request.app.state.blob_store.get(settings.albums_container, record.blob_name)
    if found is None:
        raise HTTPException(404)
    return Response(
        found[0],
        media_type=PDF,
        headers={"Content-Disposition": f'attachment; filename="{album_file_name(record.assignment.team.name)}"'},
    )


@router.delete("/{album_id}")
def delete(
    album_id: int,
    request: Request,
    session: SessionDep,
    now: NowDep,
    admin: Annotated[AdminSession, Depends(require_admin)],
    host_id: str = Depends(get_admin_host_id),
):
    """Remove the file; the team's link answers 410 from now on, until the host generates again."""
    record = _own_album(session, album_id, host_id)
    if record.deleted_at is None:
        delete_album(request.app.state.blob_store, request.app.state.settings, record, now)
        session.commit()
    return {"deleted": True}
