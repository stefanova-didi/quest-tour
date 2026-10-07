import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import func, select

from questtour.admin.crud import get_admin_host_id
from questtour.admin.errors import AdminValidationError, FieldError
from questtour.api.deps import SessionDep
from questtour.auth import AdminSession, require_admin
from questtour.clock import utc_now
from questtour.imagetypes import CONFIG_IMAGE_TYPES
from questtour.models import Assignment, Game, GameRun, Landmark, Photo, RunTask, Team
from questtour.services.game import bump

router = APIRouter(prefix="", tags=["admin-photos"])
log = logging.getLogger(__name__)


async def upload_image_blob(
    store, images_container: str, file: UploadFile, max_bytes: int
) -> str:
    ext = Path(file.filename or "").suffix.lower()
    if ext == ".jpeg":
        ext = ".jpg"
    if ext not in CONFIG_IMAGE_TYPES:
        raise AdminValidationError(
            [FieldError(field="file", message=f"unsupported image type: {ext}")]
        )
    data = await file.read()
    if len(data) > max_bytes:
        raise AdminValidationError(
            [FieldError(field="file", message=f"image exceeds {max_bytes} bytes")]
        )
    name = f"{hashlib.sha256(data).hexdigest()}{ext}"
    store.ensure_container(images_container)
    store.put(images_container, name, data, CONFIG_IMAGE_TYPES[ext], overwrite=True)
    return name


def image_public_url(settings, blob_name: str | None) -> str | None:
    if blob_name is None:
        return None
    return f"{settings.public_base_url.rstrip('/')}/api/images/{blob_name}"


class TeamPhotoOut(BaseModel):
    id: int
    team_name: str
    game_name: str
    uploaded_at: datetime
    url: str


def team_photo_download_url(settings, photo_id: int) -> str:
    return f"{settings.public_base_url.rstrip('/')}/api/admin/photos/{photo_id}/download"


@router.post("/landmarks/{id}/pictures")
async def upload_landmark_picture(
    id: int,
    request: Request,
    session: SessionDep,
    kind: Annotated[str, Form(...)],
    file: Annotated[UploadFile, File(...)],
    host_id: Annotated[str, Depends(get_admin_host_id)],
    admin: Annotated[AdminSession, Depends(require_admin)],
):
    lm = session.get(Landmark, id)
    if lm is None or lm.host_id != host_id:
        raise HTTPException(status_code=404)

    store = request.app.state.blob_store
    settings = request.app.state.settings
    name = await upload_image_blob(
        store, settings.images_container, file, settings.max_photo_bytes
    )

    old_blob: str | None = None
    if kind == "task":
        old_blob = lm.task_image
        lm.task_image = name
    elif kind == "info":
        old_blob = lm.info_image
        lm.info_image = name
    else:
        raise AdminValidationError(
            [FieldError(field="kind", message="kind must be 'task' or 'info'")]
        )

    session.commit()

    if old_blob and old_blob != name:
        # Blobs are content-addressed; only delete when no other row references them.
        other_references = session.scalar(
            select(func.count(Landmark.id)).where(
                (Landmark.task_image == old_blob) | (Landmark.info_image == old_blob)
            )
        )
        if other_references == 0:
            try:
                store.delete(settings.images_container, old_blob)
            except Exception:
                log.exception("failed to delete old landmark picture %s", old_blob)

    return {"blob_name": name, "url": image_public_url(settings, name)}


@router.get("/photos", response_model=list[TeamPhotoOut])
def list_team_photos(
    request: Request,
    session: SessionDep,
    host_id: Annotated[str, Depends(get_admin_host_id)],
    admin: Annotated[AdminSession, Depends(require_admin)],
    team_id: Annotated[int | None, None] = None,
    game_id: Annotated[int | None, None] = None,
    limit: int = 50,
    offset: int = 0,
):
    stmt = (
        select(
            Photo.id,
            Team.name.label("team_name"),
            Game.name.label("game_name"),
            Photo.uploaded_at,
        )
        .join(RunTask, Photo.run_task_id == RunTask.id)
        .join(GameRun, RunTask.run_id == GameRun.id)
        .join(Assignment, GameRun.assignment_id == Assignment.id)
        .join(Team, Assignment.team_id == Team.id)
        .join(Game, Assignment.game_id == Game.id)
        .where(Photo.deleted_at.is_(None))
        .where(Team.host_id == host_id)
        .order_by(Photo.uploaded_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if team_id is not None:
        stmt = stmt.where(Team.id == team_id)
    if game_id is not None:
        stmt = stmt.where(Game.id == game_id)

    settings = request.app.state.settings
    rows = session.execute(stmt).all()
    return [
        TeamPhotoOut(
            id=row.id,
            team_name=row.team_name,
            game_name=row.game_name,
            uploaded_at=row.uploaded_at,
            url=team_photo_download_url(settings, row.id),
        )
        for row in rows
    ]


def _photo_host_id(session, photo_id: int) -> str | None:
    row = session.execute(
        select(Team.host_id)
        .join(Assignment, Assignment.team_id == Team.id)
        .join(GameRun, GameRun.assignment_id == Assignment.id)
        .join(RunTask, RunTask.run_id == GameRun.id)
        .join(Photo, Photo.run_task_id == RunTask.id)
        .where(Photo.id == photo_id)
    ).first()
    return row.host_id if row else None


@router.delete("/photos/{id}")
def delete_team_photo(
    id: int,
    session: SessionDep,
    host_id: Annotated[str, Depends(get_admin_host_id)],
    admin: Annotated[AdminSession, Depends(require_admin)],
):
    photo = session.get(Photo, id)
    if photo is None or photo.deleted_at is not None:
        raise HTTPException(status_code=404)
    if _photo_host_id(session, id) != host_id:
        raise HTTPException(status_code=404)

    task = session.get(RunTask, photo.run_task_id)
    run = session.get(GameRun, task.run_id) if task else None
    photo.deleted_at = utc_now()
    if task and task.photo_count > 0:
        task.photo_count -= 1
    if run:
        bump(run)
    session.commit()
    return {"deleted": True}


@router.get("/photos/{id}/download")
def download_team_photo(
    id: int,
    session: SessionDep,
    request: Request,
    host_id: Annotated[str, Depends(get_admin_host_id)],
    admin: Annotated[AdminSession, Depends(require_admin)],
):
    photo = session.get(Photo, id)
    if photo is None or photo.deleted_at is not None:
        raise HTTPException(status_code=404)
    if _photo_host_id(session, id) != host_id:
        raise HTTPException(status_code=404)

    store = request.app.state.blob_store
    settings = request.app.state.settings
    result = store.get(settings.photos_container, photo.blob_name)
    if result is None:
        raise HTTPException(status_code=404)
    data, content_type = result
    return Response(content=data, media_type=content_type)
