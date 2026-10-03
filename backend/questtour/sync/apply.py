import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from questtour.imagetypes import CONFIG_IMAGE_TYPES
from questtour.models import Assignment, Game, GameTask, Landmark, Team
from questtour.storage import BlobStore
from questtour.sync.loader import LoadedConfig
from questtour.sync.schema import parse_window_time
from questtour.tokens import hash_token


@dataclass
class SyncReport:
    landmarks: int = 0
    games: int = 0
    teams: int = 0
    assignments: int = 0
    images_uploaded: int = 0
    deactivated: list[str] = field(default_factory=list)
    not_in_config: list[str] = field(default_factory=list)


def _upsert(session: Session, model, host_id: str, key: str, **values):
    obj = session.scalars(
        select(model).where(model.host_id == host_id, model.key == key)
    ).one_or_none()
    if obj is None:
        obj = model(host_id=host_id, key=key)
        session.add(obj)
    for name, value in values.items():
        setattr(obj, name, value)
    return obj


def apply_config(
    session: Session,
    store: BlobStore,
    cfg: LoadedConfig,
    *,
    host_id: str,
    images_container: str,
    photos_container: str,
) -> SyncReport:
    report = SyncReport()
    store.ensure_container(images_container)
    store.ensure_container(photos_container)

    def image(relative: str | None) -> str | None:
        if relative is None:
            return None
        path: Path = cfg.config_dir / relative
        data = path.read_bytes()
        ext = ".jpg" if path.suffix.lower() == ".jpeg" else path.suffix.lower()
        name = f"{hashlib.sha256(data).hexdigest()}{ext}"
        if not store.exists(images_container, name):
            store.put(
                images_container, name, data, CONFIG_IMAGE_TYPES[path.suffix.lower()],
                overwrite=True,
            )
            report.images_uploaded += 1
        return name

    landmarks = {}
    for lc in cfg.landmarks:
        landmarks[lc.id] = _upsert(
            session, Landmark, host_id, lc.id, name=lc.name, task_text=lc.task,
            task_image=image(lc.task_picture), accepted_answers=list(lc.accepted_answers),
            hint1=lc.hint1, hint2=lc.hint2, info_text=lc.tourist_info,
            info_image=image(lc.tourist_info_picture),
        )
    session.flush()
    games = {}
    for gc in cfg.games:
        game = _upsert(
            session, Game, host_id, gc.id, name=gc.name, intro=gc.intro, time_zone=gc.time_zone,
            max_duration_minutes=gc.max_duration_minutes,
            reveal_after_attempts=gc.reveal.attempts, reveal_after_minutes=gc.reveal.minutes,
            reveal_penalty_minutes=gc.reveal.penalty_minutes,
        )
        wanted = [landmarks[key].id for key in gc.tasks]
        if [t.landmark_id for t in game.tasks] != wanted:  # runs keep their own snapshot
            game.tasks.clear()
            session.flush()
            game.tasks.extend(GameTask(position=i, landmark_id=lid) for i, lid in enumerate(wanted))
        games[gc.id] = game
    teams = {
        tc.id: _upsert(session, Team, host_id, tc.id, name=tc.name, participants=tc.participants)
        for tc in cfg.teams
    }
    session.flush()

    seen: set[int] = set()
    zones = {gc.id: gc.time_zone for gc in cfg.games}
    for ac in cfg.assignments:
        team, game = teams[ac.team], games[ac.game]
        row = session.scalars(
            select(Assignment).where(Assignment.team_id == team.id, Assignment.game_id == game.id)
        ).one_or_none()
        if row is None:
            row = Assignment(host_id=host_id, team_id=team.id, game_id=game.id)
            session.add(row)
        row.token_hash = hash_token(ac.token)
        row.valid_from = parse_window_time(ac.valid_from, zones[ac.game])
        row.valid_until = parse_window_time(ac.valid_until, zones[ac.game])
        row.exit_message = ac.exit_message
        session.flush()
        seen.add(row.id)
    for row in session.scalars(select(Assignment).where(Assignment.host_id == host_id)):
        if row.id not in seen and row.token_hash is not None:
            row.token_hash = None  # D14: removed => link stops working
            report.deactivated.append(f"{row.team.key}/{row.game.key}")
    report.not_in_config = sorted(
        {
            f"landmark {lm.key}"
            for lm in session.scalars(select(Landmark).where(Landmark.host_id == host_id))
            if lm.key not in landmarks
        }
        | {
            f"game {g.key}"
            for g in session.scalars(select(Game).where(Game.host_id == host_id))
            if g.key not in games
        }
        | {
            f"team {t.key}"
            for t in session.scalars(select(Team).where(Team.host_id == host_id))
            if t.key not in teams
        }
    )
    report.landmarks, report.games = len(landmarks), len(games)
    report.teams, report.assignments = len(teams), len(cfg.assignments)
    return report
