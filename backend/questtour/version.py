"""Which version of the app is running (issue #29).

The deploy package carries a ``VERSION`` file at the app root, written by ``scripts/package-app.sh``
from ``git describe`` (a release tag such as ``v1.2.0``, ``v1.2.0-3-g6dd4e31`` past a tag, or a bare
commit hash before the first tag). The SPA bakes the same string into its footer at build time, and
``GET /api/health`` reports this one, so the two can be compared.
"""

from pathlib import Path

from questtour.settings import Settings

DEV_VERSION = "dev"
VERSION_FILE = Path("VERSION")  # relative to the app root, where startup.sh runs


def resolve_version(settings: Settings, version_file: Path = VERSION_FILE) -> str:
    """APP_VERSION from the environment wins; then the packaged VERSION file; else "dev"."""
    if settings.app_version and settings.app_version.strip():
        return settings.app_version.strip()
    try:
        from_file = version_file.read_text(encoding="utf-8").strip()
    except OSError:
        return DEV_VERSION
    return from_file or DEV_VERSION
