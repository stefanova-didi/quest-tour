from typing import Literal

from pydantic import BaseModel, Field

from questtour.services.game import Outcome


class HintOut(BaseModel):
    number: Literal[1, 2]
    penalty_minutes: int
    available: bool
    opened: bool
    text: str | None


class LandmarkOut(BaseModel):
    name: str
    info: str
    picture_url: str | None


class TaskOut(BaseModel):
    number: int
    text: str
    picture_url: str | None
    hints: list[HintOut]
    wrong_attempts: int
    reveal_unlocked: bool
    reveal_unlocks_in_seconds: int | None
    completion: Literal["answered", "revealed"] | None
    revealed_answer: str | None
    reveal_penalty_minutes: int  # charged on this task (0 unless revealed); frozen, unlike game.P
    landmark: LandmarkOut | None
    photo_count: int


class ClockOut(BaseModel):
    elapsed_seconds: int
    running: bool
    penalty_minutes: int
    remaining_seconds: int | None
    warning: bool


class GameOut(BaseModel):
    name: str
    intro: str
    task_count: int
    time_zone: str
    max_duration_minutes: int
    hint_penalties: list[int]
    reveal_after_attempts: int
    reveal_after_minutes: int
    reveal_penalty_minutes: int


class TeamOut(BaseModel):
    name: str


class LeaderboardRowOut(BaseModel):
    rank: int
    team_name: str
    total_seconds: int
    hints_used: int
    is_you: bool


class ResultsOut(BaseModel):
    elapsed_seconds: int
    hints_used: int
    hint_penalty_minutes: int
    reveals_used: int
    reveal_penalty_minutes: int
    total_seconds: int | None
    rank: int | None
    shared_rank: bool
    tasks_completed: int
    end_reason: Literal["finished", "max_duration", "window_closed"]
    exit_message: str
    leaderboard: list[LeaderboardRowOut]


class GameState(BaseModel):
    version: int  # game_runs.version; assignments.version_floor before Start
    service: bool  # R-25: service (test) link — no time limits, Reset available
    status: Literal["not_started", "playing", "finished", "timed_out"]
    phase: Literal["task", "photo", "info", "results"] | None
    position: int
    game: GameOut
    team: TeamOut
    clock: ClockOut | None
    task: TaskOut | None
    results: ResultsOut | None


class ActionResult(BaseModel):
    outcome: Outcome
    state: GameState


class PositionIn(BaseModel):
    position: int = Field(ge=0)


class AnswerIn(PositionIn):
    answer: str = Field(min_length=1, max_length=500)


class HintIn(PositionIn):
    hint: Literal[1, 2]


RevealIn = AdvanceIn = PositionIn
