import os

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

from questtour.sync.loader import LoadedConfig
from questtour.tokens import generate_token


def issue_tokens(
    cfg: LoadedConfig, reissue: tuple[str, str] | None = None
) -> dict[tuple[str, str], str]:
    """Generates tokens for assignments without one (and for the reissued one); mirrors them into teams_doc.
    R-25: also one service token per game in games.yaml, kept under `service.tokens`."""
    service = cfg.service
    game_ids = {g.id for g in cfg.games}
    if reissue and not (
        any((a.team, a.game) == reissue for a in cfg.assignments)
        or (service is not None and reissue[0] == service.team and reissue[1] in game_ids)
    ):
        raise ValueError(f"no assignment for team {reissue[0]!r} and game {reissue[1]!r}")
    issued: dict[tuple[str, str], str] = {}
    for index, assignment in enumerate(cfg.assignments):
        key = (assignment.team, assignment.game)
        if assignment.token is None or key == reissue:
            assignment.token = generate_token()
            cfg.teams_doc["assignments"][index]["token"] = assignment.token
            issued[key] = assignment.token
    if service is not None:
        block = cfg.teams_doc["service"]
        doc_tokens = block.get("tokens")
        if not isinstance(doc_tokens, CommentedMap):  # missing or `tokens:` left empty
            doc_tokens = block["tokens"] = CommentedMap()
        for game in cfg.games:
            key = (service.team, game.id)
            if game.id not in service.tokens or key == reissue:
                token = generate_token()
                service.tokens[game.id] = doc_tokens[game.id] = token
                issued[key] = token
        if any(key[0] == service.team for key in issued):
            doc_tokens.fa.set_block_style()  # `tokens: {}` would otherwise be dumped in flow style
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
