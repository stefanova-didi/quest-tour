import os

from ruamel.yaml import YAML

from questtour.sync.loader import LoadedConfig
from questtour.tokens import generate_token


def issue_tokens(
    cfg: LoadedConfig, reissue: tuple[str, str] | None = None
) -> dict[tuple[str, str], str]:
    """Generates tokens for assignments without one (and for the reissued one); mirrors them into teams_doc."""
    if reissue and not any((a.team, a.game) == reissue for a in cfg.assignments):
        raise ValueError(f"no assignment for team {reissue[0]!r} and game {reissue[1]!r}")
    issued: dict[tuple[str, str], str] = {}
    for index, assignment in enumerate(cfg.assignments):
        key = (assignment.team, assignment.game)
        if assignment.token is None or key == reissue:
            assignment.token = generate_token()
            cfg.teams_doc["assignments"][index]["token"] = assignment.token
            issued[key] = assignment.token
    return issued


def write_teams_file(cfg: LoadedConfig) -> None:
    """Atomic rewrite; comments and key order are preserved by ruamel round-trip mode."""
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096
    yaml.indent(mapping=2, sequence=4, offset=2)  # keep "  - team: …" as written: diff = tokens only
    path = cfg.config_dir / "teams.yaml"
    tmp = path.with_name("teams.yaml.tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as fh:
        yaml.dump(cfg.teams_doc, fh)
    os.replace(tmp, path)
