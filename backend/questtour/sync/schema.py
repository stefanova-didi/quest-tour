from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from questtour.normalize import normalize_answer

SLUG = r"^[a-z0-9][a-z0-9-]*$"


class _Cfg(BaseModel):
    # coerce_numbers_to_str: YAML reads `accepted_answers: [1879]` or `name: 1984` as numbers.
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, coerce_numbers_to_str=True)


class LandmarkCfg(_Cfg):
    id: str = Field(pattern=SLUG)
    name: str = Field(min_length=1)
    task: str = Field(min_length=1)
    task_picture: str | None = None
    accepted_answers: list[str] = Field(min_length=1)
    hint1: str | None = None
    hint2: str | None = None
    tourist_info: str = Field(min_length=1)
    tourist_info_picture: str | None = None

    @field_validator("accepted_answers")
    @classmethod
    def _answers_not_blank(cls, value: list[str]) -> list[str]:
        if any(normalize_answer(a) == "" for a in value):
            raise ValueError("an accepted answer is empty after normalisation")
        return value

    @model_validator(mode="after")
    def _hint2_needs_hint1(self) -> "LandmarkCfg":
        if self.hint2 and not self.hint1:
            raise ValueError("hint2 is set but hint1 is empty")
        return self


class RevealCfg(_Cfg):
    attempts: int = Field(5, ge=1)
    minutes: int = Field(20, ge=0)
    penalty_minutes: int = Field(30, ge=0)


class GameCfg(_Cfg):
    id: str = Field(pattern=SLUG)
    name: str = Field(min_length=1)
    intro: str = Field(min_length=1)
    time_zone: str
    max_duration_minutes: int = Field(gt=0)
    reveal: RevealCfg = Field(default_factory=RevealCfg)
    tasks: list[str] = Field(min_length=1)

    @field_validator("time_zone")
    @classmethod
    def _valid_zone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(f"unknown time zone {value!r}") from exc
        return value

    @field_validator("tasks")
    @classmethod
    def _no_repeats(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value):
            raise ValueError("a landmark appears twice in the task list")
        return value


class TeamCfg(_Cfg):
    id: str = Field(pattern=SLUG)
    name: str = Field(min_length=1)
    participants: int | None = Field(default=None, ge=1)


class AssignmentCfg(_Cfg):
    team: str
    game: str
    valid_from: str
    valid_until: str
    exit_message: str = ""
    token: str | None = Field(default=None, min_length=22)  # >= 128 bits base64url

    @field_validator("valid_from", "valid_until", mode="before")
    @classmethod
    def _quoted(cls, value):
        if isinstance(value, (datetime, date)):
            raise ValueError(  # noqa: TRY004 - pydantic reports ValueError as a validation error
                'write the timestamp in quotes, e.g. "2026-10-14T09:00:00+03:00"'
            )
        return value


def parse_window_time(value: str, time_zone: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=ZoneInfo(time_zone))
