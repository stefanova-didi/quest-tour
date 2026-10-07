from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError

from questtour.admin.crud import get_admin_host_id, handle_integrity, require_fresh
from questtour.admin.schemas import LandmarkCreate, LandmarkOut, LandmarkUpdate, _validate_landmark
from questtour.api.deps import SessionDep
from questtour.auth import AdminSession, require_admin
from questtour.models import GameTask, Landmark, RunTask

router = APIRouter(prefix="/landmarks", tags=["admin-landmarks"])


@router.get("", response_model=list[LandmarkOut])
def list_landmarks(
    session: SessionDep,
    admin: Annotated[AdminSession, Depends(require_admin)],
    host_id: str = Depends(get_admin_host_id),
    q: str = "",
):
    stmt = select(Landmark).where(Landmark.host_id == host_id)
    if q:
        stmt = stmt.where(Landmark.name.ilike(f"%{q}%") | Landmark.key.ilike(f"%{q}%"))
    return session.scalars(stmt.order_by(Landmark.name)).all()


@router.post("", response_model=LandmarkOut, status_code=201)
def create_landmark(
    data: LandmarkCreate,
    session: SessionDep,
    admin: Annotated[AdminSession, Depends(require_admin)],
    host_id: str = Depends(get_admin_host_id),
):
    _validate_landmark(data)
    lm = Landmark(
        host_id=host_id,
        key=data.key,
        name=data.name,
        task_text=data.task,
        accepted_answers=data.accepted_answers,
        hint1=data.hint1,
        hint2=data.hint2,
        info_text=data.tourist_info,
        coordinates_lat=data.coordinates.lat if data.coordinates else None,
        coordinates_lon=data.coordinates.lon if data.coordinates else None,
    )
    session.add(lm)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise handle_integrity(exc, {"key": "key"})
    return lm


@router.get("/{id}", response_model=LandmarkOut)
def get_landmark(
    id: int,
    session: SessionDep,
    admin: Annotated[AdminSession, Depends(require_admin)],
    host_id: str = Depends(get_admin_host_id),
):
    lm = session.get(Landmark, id)
    if lm is None or lm.host_id != host_id:
        raise HTTPException(status_code=404)
    return lm


@router.put("/{id}", response_model=LandmarkOut)
def update_landmark(
    id: int,
    data: LandmarkUpdate,
    session: SessionDep,
    admin: Annotated[AdminSession, Depends(require_admin)],
    host_id: str = Depends(get_admin_host_id),
):
    lm = session.get(Landmark, id)
    if lm is None or lm.host_id != host_id:
        raise HTTPException(status_code=404)
    require_fresh(lm, data.seen_at)
    _validate_landmark(data)
    lm.key = data.key
    lm.name = data.name
    lm.task_text = data.task
    lm.accepted_answers = data.accepted_answers
    lm.hint1 = data.hint1
    lm.hint2 = data.hint2
    lm.info_text = data.tourist_info
    lm.coordinates_lat = data.coordinates.lat if data.coordinates else None
    lm.coordinates_lon = data.coordinates.lon if data.coordinates else None
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise handle_integrity(exc, {"key": "key"})
    return lm


@router.delete("/{id}")
def delete_landmark(
    id: int,
    session: SessionDep,
    admin: Annotated[AdminSession, Depends(require_admin)],
    host_id: str = Depends(get_admin_host_id),
    force: bool = False,
):
    lm = session.get(Landmark, id)
    if lm is None or lm.host_id != host_id:
        raise HTTPException(status_code=404)

    games_using = session.scalars(
        select(GameTask.game_id).where(GameTask.landmark_id == id).distinct()
    ).all()

    # Run snapshots are immutable: any historical reference blocks deletion.
    run_references = session.scalar(
        select(func.count(RunTask.id)).where(RunTask.landmark_id == id)
    )
    if run_references:
        raise HTTPException(
            status_code=409,
            detail="cannot delete a landmark used by a finished or active run",
        )

    if games_using and not force:
        return JSONResponse(status_code=409, content={"used_by_games": games_using})

    # Safe to remove GameTask references: runs keep their own snapshot.
    if games_using:
        session.execute(delete(GameTask).where(GameTask.landmark_id == id))

    session.delete(lm)
    session.commit()
    return {"deleted": True}
