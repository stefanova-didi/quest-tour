from datetime import datetime, timedelta
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.orm import Session

from questtour.models import AnswerAttempt, Assignment, Game, GameRun, RunDevice, RunTask
from questtour.normalize import is_correct

HINT_PENALTIES: dict[int, int] = {1: 10, 2: 15}   # R-4 (fixed, not per game)
COMPASS_PENALTY_MINUTES: int = 5                   # R-26
WARNING_SECONDS = 15 * 60                         # R-8, R-14
TIMED_OUT = frozenset({"max_duration", "window_closed"})


class Outcome(StrEnum):
    OK = "ok"
    ALREADY_STARTED = "already_started"
    CORRECT = "correct"
    WRONG = "wrong"
    STALE = "stale"
    LOCKED = "locked"
    NOT_AVAILABLE = "not_available"
    GAME_OVER = "game_over"


def load_run(session: Session, assignment_id: int) -> GameRun | None:
    """Locks the run row: every action is serialised per team (technical §3, R-18)."""
    stmt = select(GameRun).where(GameRun.assignment_id == assignment_id).with_for_update()
    return session.scalars(stmt).one_or_none()


def current_task(run: GameRun) -> RunTask | None:
    return run.tasks[run.current_position] if run.current_position < len(run.tasks) else None


def run_status(run: GameRun) -> str:
    if run.end_reason is None:
        return "playing"
    return "finished" if run.end_reason == "finished" else "timed_out"


def effective_deadline(run: GameRun, assignment: Assignment) -> tuple[datetime, str]:
    by_duration = run.started_at + timedelta(minutes=assignment.game.max_duration_minutes)
    if assignment.valid_until < by_duration:
        return assignment.valid_until, "window_closed"
    return by_duration, "max_duration"


def is_service(assignment: Assignment) -> bool:
    """R-25: a service (test) team's links ignore every time limit and can be reset."""
    return assignment.team.is_service


def apply_time_limits(run: GameRun, assignment: Assignment, now: datetime) -> None:
    """R-8: called on every request; the end time is the deadline itself, not the request time.
    Service runs (R-25) never end by time."""
    if run.end_reason is not None or is_service(assignment):
        return
    end_at, reason = effective_deadline(run, assignment)
    if now >= end_at:
        run.ended_at, run.end_reason = end_at, reason
        bump(run)


def bump(run: GameRun) -> None:
    """Every write that changes what players see increments the version (client ordering, §9.4)."""
    run.version += 1


def elapsed_seconds(run: GameRun, now: datetime) -> int:
    return max(0, int(((run.ended_at or now) - run.started_at).total_seconds()))


def penalty_minutes(run: GameRun) -> int:
    return sum(t.hint_penalty_minutes + t.reveal_penalty_minutes for t in run.tasks)


def hints_used(run: GameRun) -> int:
    # R-12: the leaderboard "hints used" column counts hints + compasses.
    return sum(
        (t.hint1_at is not None) + (t.hint2_at is not None) + (t.compass_opened_at is not None)
        for t in run.tasks
    )


def total_seconds(run: GameRun) -> int:
    """R-7: (finish - start) + penalties. Only meaningful for finished runs."""
    assert run.finished_at is not None
    return int((run.finished_at - run.started_at).total_seconds()) + 60 * penalty_minutes(run)


def reveal_unlocked(task: RunTask, game: Game, now: datetime, *, instant: bool = False) -> bool:
    """R-6: after N wrong attempts or X minutes on the task, whichever comes first.
    `instant` (service links, R-25) unlocks it as soon as the task is shown."""
    return (
        instant
        or task.wrong_attempts >= game.reveal_after_attempts
        or now >= task.shown_at + timedelta(minutes=game.reveal_after_minutes)
    )


def touch_device(session: Session, run: GameRun, device_id: str | None, now: datetime) -> None:
    if device_id is None:
        return
    device = session.get(RunDevice, (run.id, device_id))
    if device is None:
        session.add(
            RunDevice(run_id=run.id, device_id=device_id, first_seen_at=now, last_seen_at=now)
        )
    else:
        device.last_seen_at = now


def start_run(session: Session, assignment: Assignment, now: datetime) -> GameRun:
    """Caller holds the assignment row lock and has checked no run exists. Snapshots the landmark order.
    Starts above assignment.version_floor so a reset (R-25) never makes phones drop newer states."""
    run = GameRun(
        assignment=assignment,
        started_at=now,
        current_position=0,
        version=assignment.version_floor + 1,
    )
    for position, game_task in enumerate(assignment.game.tasks):
        run.tasks.append(
            RunTask(
                position=position,
                landmark_id=game_task.landmark_id,
                hint_penalty_minutes=0,
                reveal_penalty_minutes=0,
                wrong_attempts=0,
                photo_count=0,
            )
        )
    run.tasks[0].shown_at = now
    session.add(run)
    session.flush()
    return run


def _open_task(run: GameRun, position: int) -> tuple[RunTask | None, Outcome | None]:
    if run.end_reason in TIMED_OUT:
        return None, Outcome.GAME_OVER
    task = current_task(run)
    if run.current_position != position or task is None or task.completed_at is not None:
        return None, Outcome.STALE
    return task, None


def _complete(run: GameRun, task: RunTask, kind: str, now: datetime) -> None:
    task.completed_at, task.completion = now, kind
    bump(run)
    if task.position == len(run.tasks) - 1:          # R-2: clock stops at the last completion
        run.finished_at = run.ended_at = now
        run.end_reason = "finished"


def submit_answer(
    session: Session,
    run: GameRun,
    position: int,
    answer: str,
    now: datetime,
    device_id: str | None,
) -> Outcome:
    task, blocked = _open_task(run, position)
    if blocked:
        if blocked == Outcome.STALE and 0 <= position < len(run.tasks):   # R-5: log teammates' late answers too
            late = run.tasks[position]
            session.add(
                AnswerAttempt(
                    run_task_id=late.id,
                    device_id=device_id,
                    submitted_at=now,
                    answer_text=answer,
                    correct=is_correct(answer, late.landmark.accepted_answers),
                )
            )
        return blocked
    correct = is_correct(answer, task.landmark.accepted_answers)
    session.add(
        AnswerAttempt(
            run_task_id=task.id,
            device_id=device_id,
            submitted_at=now,
            answer_text=answer,
            correct=correct,
        )
    )                                                  # R-5: every attempt logged
    if not correct:
        task.wrong_attempts += 1
        bump(run)                                      # wrong_attempts may unlock Reveal on other phones
        return Outcome.WRONG
    _complete(run, task, "answered", now)
    return Outcome.CORRECT


def open_hint(run: GameRun, position: int, number: int, now: datetime) -> Outcome:
    task, blocked = _open_task(run, position)
    if blocked:
        return blocked
    landmark = task.landmark
    text = landmark.hint1 if number == 1 else landmark.hint2
    if not text or (number == 2 and task.hint1_at is None):
        return Outcome.NOT_AVAILABLE
    attr = "hint1_at" if number == 1 else "hint2_at"
    if getattr(task, attr) is None:                    # R-18: charged at most once
        setattr(task, attr, now)
        task.hint_penalty_minutes += HINT_PENALTIES[number]
        bump(run)
    return Outcome.OK


def open_compass(run: GameRun, now: datetime) -> Outcome:
    task, blocked = _open_task(run, run.current_position)
    if blocked:
        return blocked
    if task.landmark.coordinates_lat is None or task.landmark.coordinates_lon is None:
        return Outcome.NOT_AVAILABLE
    if task.compass_opened_at is None:  # R-18/R-26: charged at most once
        task.compass_opened_at = now
        task.hint_penalty_minutes += COMPASS_PENALTY_MINUTES
        bump(run)
    return Outcome.OK


def reveal_answer(
    run: GameRun, game: Game, position: int, now: datetime, *, instant: bool = False
) -> Outcome:
    task, blocked = _open_task(run, position)
    if blocked:
        return blocked
    if not reveal_unlocked(task, game, now, instant=instant):
        return Outcome.LOCKED
    task.revealed_at = now
    task.reveal_penalty_minutes = game.reveal_penalty_minutes   # frozen at charge time
    _complete(run, task, "revealed", now)
    return Outcome.OK


def advance(run: GameRun, position: int, now: datetime, *, service: bool = False) -> Outcome:
    """'Next riddle' / 'See results' (D1). Requires completion + at least one photo (R-1, R-10).

    Service runs (R-25) may advance without a photo: for the test team the photo is optional.
    """
    if run.end_reason in TIMED_OUT:
        return Outcome.GAME_OVER
    task = current_task(run)
    if run.current_position != position or task is None:
        return Outcome.STALE
    if task.completed_at is None or (task.photo_count == 0 and not service):
        return Outcome.LOCKED
    run.current_position += 1
    bump(run)
    following = current_task(run)
    if following is not None:
        following.shown_at = now
    return Outcome.OK
