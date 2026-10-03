import re
from datetime import UTC, datetime

from questtour.safenames import photo_blob_name, safe_name


def test_safe_name():
    assert safe_name("Sofia Old Town Quest") == "Sofia-Old-Town-Quest"
    assert safe_name("Café Ñoño") == "Cafe-Nono"
    assert safe_name("Lost & Found") == "Lost-Found"
    assert re.fullmatch(r"[A-Za-z0-9_-]+", safe_name("Александър Невски"))
    assert safe_name("!!!") == "unnamed"


def test_photo_blob_name_matches_r10_pattern():
    at = datetime(2026, 10, 14, 11, 32, 5, tzinfo=UTC)
    assert photo_blob_name("Sofia-Center", "The Explorers", at, 3, "Alexander Nevsky", "jpg") == \
        "Sofia-Center/The-Explorers/2026-10-14_11-32-05_03_Alexander-Nevsky.jpg"
    assert photo_blob_name("G", "T", at, 3, "L", "jpg", suffix=2).endswith("_03_L_2.jpg")
