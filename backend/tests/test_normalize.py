import pytest

from questtour.normalize import is_correct, normalize_answer


@pytest.mark.parametrize(("raw", "expected"), [
    ("  Alexander   Nevsky Cathedral!! ", "alexander nevsky cathedral"),
    ("Alexander-Nevsky", "alexander nevsky"),
    ("St. Paul's", "st pauls"),
    ("Catedral Nevský", "catedral nevsky"),
    ("ÉGLISE", "eglise"),
    ("Александър Невски", "александър невски"),      # Cyrillic kept, only lower-cased
    ("Свети Николай", "свети николаи"),              # й = и + combining breve -> breve stripped
])
def test_normalize(raw, expected):
    assert normalize_answer(raw) == expected


def test_is_correct_matches_any_accepted_answer():
    accepted = ["Alexander Nevsky Cathedral", "Alexander Nevsky"]
    assert is_correct("alexander nevsky", accepted)
    assert is_correct("ALEXANDER-NEVSKY cathedral.", accepted)
    assert not is_correct("Saint Sofia Church", accepted)
    assert not is_correct("   !!! ", accepted)
