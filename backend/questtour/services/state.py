import math
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from questtour.api.schemas import (
    ClockOut,
    GameOut,
    GameState,
    HintOut,
    LandmarkOut,
    ResultsOut,
    TaskOut,
    TeamOut,
)
from questtour.models import Assignment, Game, GameRun, RunTask
from questtour.services.game import (
    HINT_PENALTIES,
    TIMED_OUT,
    WARNING_SECONDS,
    apply_time_limits,
    current_task,
    effective_deadline,
    elapsed_seconds,
    hints_used,
    is_service,
    penalty_minutes,
    reveal_unlocked,
    run_status,
    total_seconds,
)
from questtour.services.leaderboard import leaderboard_rows


def image_url(blob_name: str | None) -> str | None:
    return f"/api/images/{blob_name}" if blob_name else None


def run_phase(run: GameRun, assignment: Assignment, now: datetime) -> str:
    if run.end_reason in TIMED_OUT:
        return "results"
    task = current_task(run)
    if task is None:
        return "results"
    if run.end_reason == "finished" and not is_service(assignment) and now >= assignment.valid_until:
        return "results"  # finished team re-opening after the window: straight to Finish
    if task.completed_at is None:
        return "task"
    return "photo" if task.photo_count == 0 else "info"


def build_game(game: Game, task_count: int) -> GameOut:
    return GameOut(
        name=game.name,
        intro=game.intro,
        task_count=task_count,
        time_zone=game.time_zone,
        max_duration_minutes=game.max_duration_minutes,
        hint_penalties=[HINT_PENALTIES[1], HINT_PENALTIES[2]],
        reveal_after_attempts=game.reveal_after_attempts,
        reveal_after_minutes=game.reveal_after_minutes,
        reveal_penalty_minutes=game.reveal_penalty_minutes,
    )


def build_clock(run: GameRun, assignment: Assignment, now: datetime) -> ClockOut:
    running = run.end_reason is None
    remaining = None
    if running and not is_service(assignment):  # R-25: service runs have no deadline
        end_at, _ = effective_deadline(run, assignment)
        # Rounded UP: 0 only once the deadline has passed (and then apply_time_limits has already ended
        # the run). Flooring would send `running: true, remaining_seconds: 0` during the last second, and
        # GameHeader would re-request on every response until the deadline (§10.1 onTimeUp).
        remaining = max(0, math.ceil((end_at - now).total_seconds()))
    return ClockOut(
        elapsed_seconds=elapsed_seconds(run, now),
        running=running,
        penalty_minutes=penalty_minutes(run),
        remaining_seconds=remaining,
        warning=remaining is not None and remaining <= WARNING_SECONDS,
    )


def build_task(task: RunTask, game: Game, now: datetime, *, instant: bool = False) -> TaskOut:
    landmark = task.landmark
    completed = task.completed_at is not None
    hints: list[HintOut] = []
    for number, text, opened_at in (
        (1, landmark.hint1, task.hint1_at),
        (2, landmark.hint2, task.hint2_at),
    ):
        if not text and opened_at is None:
            continue
        opened = opened_at is not None
        hints.append(
            HintOut(
                number=number,
                penalty_minutes=HINT_PENALTIES[number],
                opened=opened,
                available=not opened and not completed and (number == 1 or task.hint1_at is not None),
                text=(text or "") if opened else None,  # unopened hint text never leaves the server
            )
        )
    unlocked = not completed and reveal_unlocked(task, game, now, instant=instant)
    unlocks_in = None
    if not completed and not unlocked:
        due = task.shown_at + timedelta(minutes=game.reveal_after_minutes)
        unlocks_in = max(0, math.ceil((due - now).total_seconds()))
    return TaskOut(
        number=task.position + 1,
        text=landmark.task_text,
        picture_url=image_url(landmark.task_image),
        hints=hints,
        wrong_attempts=task.wrong_attempts,
        reveal_unlocked=unlocked,
        reveal_unlocks_in_seconds=unlocks_in,
        completion=task.completion,
        revealed_answer=landmark.accepted_answers[0] if task.completion == "revealed" else None,
        reveal_penalty_minutes=task.reveal_penalty_minutes,
        landmark=LandmarkOut(
            name=landmark.name,
            info=landmark.info_text,
            picture_url=image_url(landmark.info_image),
        )
        if completed
        else None,
        photo_count=task.photo_count,
    )


def build_results(
    session: Session, run: GameRun, assignment: Assignment, now: datetime
) -> ResultsOut:
    rows = leaderboard_rows(session, assignment.game_id, viewer_run_id=run.id)
    me = next((row for row in rows if row.is_you), None)
    return ResultsOut(
        elapsed_seconds=elapsed_seconds(run, now),
        hints_used=hints_used(run),
        hint_penalty_minutes=sum(t.hint_penalty_minutes for t in run.tasks),
        reveals_used=sum(1 for t in run.tasks if t.revealed_at is not None),
        reveal_penalty_minutes=sum(t.reveal_penalty_minutes for t in run.tasks),
        total_seconds=total_seconds(run) if run.end_reason == "finished" else None,
        rank=me.rank if me else None,
        shared_rank=me is not None and sum(1 for row in rows if row.rank == me.rank) > 1,
        tasks_completed=sum(1 for t in run.tasks if t.completed_at is not None),
        end_reason=run.end_reason,
        exit_message=assignment.exit_message,
        leaderboard=rows,
    )


def build_state(
    session: Session, assignment: Assignment, run: GameRun | None, now: datetime
) -> GameState:
    game, team = assignment.game, assignment.team
    service = is_service(assignment)
    if run is None:
        return GameState(
            version=assignment.version_floor,
            service=service,
            status="not_started",
            phase=None,
            position=0,
            game=build_game(game, len(game.tasks)),
            team=TeamOut(name=team.name),
            clock=None,
            task=None,
            results=None,
        )
    apply_time_limits(run, assignment, now)
    phase = run_phase(run, assignment, now)
    task = current_task(run) if phase != "results" else None
    return GameState(
        version=run.version,
        service=service,
        status=run_status(run),
        phase=phase,
        position=run.current_position,
        game=build_game(game, len(run.tasks)),
        team=TeamOut(name=team.name),
        clock=build_clock(run, assignment, now),
        task=build_task(task, game, now, instant=service) if task is not None else None,
        results=build_results(session, run, assignment, now) if phase == "results" else None,
    )
