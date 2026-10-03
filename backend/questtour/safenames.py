import re
from datetime import datetime

from unidecode import unidecode

_SPACES = re.compile(r"\s+")
_UNSAFE = re.compile(r"[^A-Za-z0-9_-]+")
_DASHES = re.compile(r"-{2,}")


def safe_name(text: str) -> str:
    """Latin transliteration, spaces -> '-', only [A-Za-z0-9_-] kept (R-10)."""
    value = _SPACES.sub("-", unidecode(text).strip())
    value = _DASHES.sub("-", _UNSAFE.sub("", value)).strip("-_")
    return value or "unnamed"


def photo_blob_name(game_name: str, team_name: str, uploaded_local: datetime, task_no: int,
                    landmark_name: str, ext: str, suffix: int = 1) -> str:
    stem = f"{uploaded_local:%Y-%m-%d_%H-%M-%S}_{task_no:02d}_{safe_name(landmark_name)}"
    if suffix > 1:
        stem = f"{stem}_{suffix}"
    return f"{safe_name(game_name)}/{safe_name(team_name)}/{stem}.{ext}"
