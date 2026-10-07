from questtour.settings import Settings
from questtour.storage import BlobStore
from questtour.sync.apply import SyncReport, apply_config
from questtour.sync.loader import load_config
from questtour.sync.teams_file import issue_tokens, write_teams_file


def import_yaml(
    *,
    session,
    store: BlobStore,
    settings: Settings,
    write_back: bool = True,
    autocommit: bool = True,
    reissue: tuple[str, str] | None = None,
) -> SyncReport | list[str]:
    """Load YAML config and apply it to the database.

    Returns a list of validation error strings if the config is invalid, otherwise
    a ``SyncReport``. When ``write_back`` is True, newly generated tokens are written
    back to ``teams.yaml``. When ``autocommit`` is True the database transaction is
    committed before returning.
    """
    cfg = load_config(settings.config_dir)
    if cfg.errors:
        return cfg.errors
    try:
        issued = issue_tokens(cfg, reissue)
    except ValueError as exc:
        return [str(exc)]
    if write_back:
        write_teams_file(cfg)
    report = apply_config(
        session,
        store,
        cfg,
        host_id=settings.host_id,
        images_container=settings.images_container,
        photos_container=settings.photos_container,
    )
    report.issued = issued
    if autocommit:
        session.commit()
    return report
