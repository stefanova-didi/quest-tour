from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel, ValidationError
from ruamel.yaml import YAML

from questtour.imagetypes import CONFIG_IMAGE_TYPES
from questtour.safenames import safe_name
from questtour.sync.schema import (
    AssignmentCfg,
    GameCfg,
    LandmarkCfg,
    TeamCfg,
    parse_window_time,
)


@dataclass
class LoadedConfig:
    config_dir: Path
    landmarks: list[LandmarkCfg] = field(default_factory=list)
    games: list[GameCfg] = field(default_factory=list)
    teams: list[TeamCfg] = field(default_factory=list)
    assignments: list[AssignmentCfg] = field(default_factory=list)
    teams_doc: object = None  # ruamel round-trip document, for token write-back
    errors: list[str] = field(default_factory=list)


def _read(path: Path, yaml: YAML, errors: list[str]):
    if not path.is_file():
        errors.append(f"{path.name}: file not found (looked in {path.resolve()})")
        return None
    try:
        return yaml.load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # noqa: BLE001 - ruamel raises several parser error types
        errors.append(f"{path.name}: invalid YAML: {exc}")
        return None


def _parse_list(doc, file: str, key: str, model: type[BaseModel], errors: list[str]) -> list:
    items = (doc or {}).get(key) or []
    parsed = []
    for index, raw in enumerate(items):
        try:
            parsed.append(model.model_validate(dict(raw)))
        except (ValidationError, TypeError, ValueError) as exc:
            label = raw.get("id") if hasattr(raw, "get") else None
            if isinstance(exc, ValidationError):
                details = exc.errors()
            else:
                details = [{"loc": (), "msg": str(exc)}]
            for err in details:
                where = ".".join(str(p) for p in err["loc"])
                errors.append(
                    f"{file}: {key}[{index}]{f' ({label})' if label else ''} {where}: {err['msg']}"
                )
    return parsed


def _duplicates(file: str, what: str, values: list[str]) -> list[str]:
    seen, out = set(), []
    for v in values:
        if v in seen:
            out.append(f"{file}: duplicate {what} {v!r}")
        seen.add(v)
    return out


def load_config(config_dir: Path) -> LoadedConfig:
    cfg = LoadedConfig(config_dir=config_dir)
    safe, round_trip = YAML(typ="safe"), YAML()
    round_trip.preserve_quotes = True
    landmarks_doc = _read(config_dir / "landmarks.yaml", safe, cfg.errors)
    games_doc = _read(config_dir / "games.yaml", safe, cfg.errors)
    cfg.teams_doc = _read(config_dir / "teams.yaml", round_trip, cfg.errors)
    cfg.landmarks = _parse_list(landmarks_doc, "landmarks.yaml", "landmarks", LandmarkCfg, cfg.errors)
    cfg.games = _parse_list(games_doc, "games.yaml", "games", GameCfg, cfg.errors)
    cfg.teams = _parse_list(cfg.teams_doc, "teams.yaml", "teams", TeamCfg, cfg.errors)
    cfg.assignments = _parse_list(
        cfg.teams_doc, "teams.yaml", "assignments", AssignmentCfg, cfg.errors
    )
    if not cfg.errors:
        cfg.errors.extend(cross_check(cfg))
    return cfg


def cross_check(cfg: LoadedConfig) -> list[str]:
    errors: list[str] = []
    errors += _duplicates("landmarks.yaml", "landmark id", [lm.id for lm in cfg.landmarks])
    errors += _duplicates("games.yaml", "game id", [g.id for g in cfg.games])
    errors += _duplicates("teams.yaml", "team id", [t.id for t in cfg.teams])
    errors += _duplicates("teams.yaml", "team name", [t.name.casefold() for t in cfg.teams])
    # R-10 folders use safe_name(): "The Explorers" and "The-Explorers" would share a photo folder
    errors += _duplicates(
        "teams.yaml", "team photo-folder name", [safe_name(t.name).casefold() for t in cfg.teams]
    )
    errors += _duplicates(
        "games.yaml", "game photo-folder name", [safe_name(g.name).casefold() for g in cfg.games]
    )
    errors += _duplicates(
        "teams.yaml", "assignment", [f"{a.team}/{a.game}" for a in cfg.assignments]
    )
    errors += _duplicates("teams.yaml", "token", [a.token for a in cfg.assignments if a.token])
    landmark_ids = {lm.id for lm in cfg.landmarks}
    for game in cfg.games:
        errors += [
            f"games.yaml: game {game.id!r} uses unknown landmark {t!r}"
            for t in game.tasks
            if t not in landmark_ids
        ]
    for lm in cfg.landmarks:
        for picture in (lm.task_picture, lm.tourist_info_picture):
            if picture is None:
                continue
            path = cfg.config_dir / picture
            if not path.is_file():
                errors.append(f"landmarks.yaml: landmark {lm.id!r} picture not found: {picture}")
            elif path.suffix.lower() not in CONFIG_IMAGE_TYPES:
                errors.append(
                    f"landmarks.yaml: landmark {lm.id!r} picture type not supported: {picture}"
                )
    teams = {t.id for t in cfg.teams}
    zones = {g.id: g.time_zone for g in cfg.games}
    for a in cfg.assignments:
        if a.team not in teams:
            errors.append(f"teams.yaml: assignment {a.team}/{a.game} uses unknown team {a.team!r}")
        if a.game not in zones:
            errors.append(f"teams.yaml: assignment {a.team}/{a.game} uses unknown game {a.game!r}")
            continue
        try:
            start = parse_window_time(a.valid_from, zones[a.game])
            end = parse_window_time(a.valid_until, zones[a.game])
        except ValueError as exc:
            errors.append(f"teams.yaml: assignment {a.team}/{a.game}: bad timestamp: {exc}")
            continue
        if start >= end:
            errors.append(
                f"teams.yaml: assignment {a.team}/{a.game}: valid_from must be before valid_until"
            )
    return errors
