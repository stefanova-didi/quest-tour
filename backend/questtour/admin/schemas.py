from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, computed_field, model_validator

from questtour.admin.errors import AdminValidationError, _pydantic_errors
from questtour.models import Landmark
from questtour.sync.schema import GameBaseCfg, LandmarkBaseCfg, TeamBaseCfg

SLUG = r"^[a-z0-9][a-z0-9-]*$"


class CoordinatesIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class LandmarkCreate(BaseModel):
    key: str = Field(pattern=SLUG)
    name: str = Field(min_length=1)
    name_i18n: dict[str, str] | None = None
    task: str = Field(min_length=1)
    task_i18n: dict[str, str] | None = None
    accepted_answers: list[str] = Field(min_length=1)
    hint1: str | None = None
    hint1_i18n: dict[str, str] | None = None
    hint2: str | None = None
    hint2_i18n: dict[str, str] | None = None
    tourist_info: str = Field(min_length=1)
    tourist_info_i18n: dict[str, str] | None = None
    coordinates: CoordinatesIn | None = None


class LandmarkUpdate(LandmarkCreate):
    seen_at: datetime | None = None


class LandmarkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    name: str
    name_i18n: dict[str, str] | None
    task: str
    task_i18n: dict[str, str] | None
    accepted_answers: list[str]
    hint1: str | None
    hint1_i18n: dict[str, str] | None
    hint2: str | None
    hint2_i18n: dict[str, str] | None
    tourist_info: str
    tourist_info_i18n: dict[str, str] | None
    coordinates: CoordinatesIn | None
    updated_at: datetime
    task_image: str | None = Field(exclude=True)
    info_image: str | None = Field(exclude=True)

    @model_validator(mode="before")
    @classmethod
    def _from_landmark(cls, data: Any) -> Any:
        if isinstance(data, Landmark):
            coords = None
            if data.coordinates_lat is not None and data.coordinates_lon is not None:
                coords = {"lat": data.coordinates_lat, "lon": data.coordinates_lon}
            return {
                "id": data.id,
                "key": data.key,
                "name": data.name,
                "name_i18n": data.name_i18n,
                "task": data.task_text,
                "task_i18n": data.task_text_i18n,
                "accepted_answers": data.accepted_answers,
                "hint1": data.hint1,
                "hint1_i18n": data.hint1_i18n,
                "hint2": data.hint2,
                "hint2_i18n": data.hint2_i18n,
                "tourist_info": data.info_text,
                "tourist_info_i18n": data.info_text_i18n,
                "coordinates": coords,
                "task_image": data.task_image,
                "info_image": data.info_image,
                "updated_at": data.updated_at,
            }
        return data

    @computed_field
    @property
    def task_image_url(self) -> str | None:
        return f"/api/images/{self.task_image}" if self.task_image else None

    @computed_field
    @property
    def info_image_url(self) -> str | None:
        return f"/api/images/{self.info_image}" if self.info_image else None


class RevealSettings(BaseModel):
    attempts: int = Field(5, ge=1)
    minutes: int = Field(20, ge=0)
    penalty_minutes: int = Field(30, ge=0)


class GameCreate(BaseModel):
    key: str = Field(pattern=SLUG)
    name: str = Field(min_length=1)
    intro: str = Field(min_length=1)
    time_zone: str
    max_duration_minutes: int = Field(gt=0)
    reveal: RevealSettings = Field(default_factory=RevealSettings)


class GameUpdate(GameCreate):
    seen_at: datetime | None = None


class GameOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    name: str
    intro: str
    time_zone: str
    max_duration_minutes: int
    reveal: RevealSettings
    updated_at: datetime
    task_landmark_ids: list[int]
    available_languages: list[str]


class GameTasksUpdate(BaseModel):
    landmark_ids: list[int] = Field(min_length=1)
    seen_at: datetime | None = None


class TeamCreate(BaseModel):
    key: str = Field(pattern=SLUG)
    name: str = Field(min_length=1)
    participants: int | None = Field(default=None, ge=1)


class TeamUpdate(TeamCreate):
    seen_at: datetime | None = None


class TeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    name: str
    participants: int | None
    updated_at: datetime


class AssignmentCreate(BaseModel):
    game_id: int
    valid_from: str
    valid_until: str
    exit_message: str = ""


class TeamAssignmentsUpdate(BaseModel):
    assignments: list[AssignmentCreate]
    seen_at: datetime | None = None


class AssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    game_id: int
    game_name: str
    valid_from: datetime
    valid_until: datetime
    exit_message: str
    token_issued: bool
    issued_at: datetime | None
    updated_at: datetime


class TokenReveal(BaseModel):
    assignment_id: int
    token: str
    url: str


def _validate_team(data: TeamCreate) -> None:
    try:
        TeamBaseCfg.model_validate({
            "id": data.key,
            "name": data.name,
            "participants": data.participants,
        })
    except ValidationError as exc:
        raise AdminValidationError(_pydantic_errors(exc)) from exc


def _validate_landmark(data: LandmarkCreate) -> None:
    try:
        LandmarkBaseCfg.model_validate({
            "id": data.key,
            "name": data.name,
            "name_i18n": data.name_i18n,
            "task": data.task,
            "task_i18n": data.task_i18n,
            "accepted_answers": data.accepted_answers,
            "hint1": data.hint1,
            "hint1_i18n": data.hint1_i18n,
            "hint2": data.hint2,
            "hint2_i18n": data.hint2_i18n,
            "tourist_info": data.tourist_info,
            "tourist_info_i18n": data.tourist_info_i18n,
            "coordinates": data.coordinates.model_dump() if data.coordinates else None,
        })
    except ValidationError as exc:
        raise AdminValidationError(_pydantic_errors(exc)) from exc


def _validate_game(data: GameCreate) -> None:
    try:
        GameBaseCfg.model_validate({
            "id": data.key,
            "name": data.name,
            "intro": data.intro,
            "time_zone": data.time_zone,
            "max_duration_minutes": data.max_duration_minutes,
            "reveal": data.reveal.model_dump(),
        })
    except ValidationError as exc:
        raise AdminValidationError(_pydantic_errors(exc)) from exc
