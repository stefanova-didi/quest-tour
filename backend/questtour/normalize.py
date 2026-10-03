"""Answer normalisation (R-9): case, whitespace, punctuation and diacritics are ignored."""
import re
import unicodedata
from collections.abc import Iterable

_WHITESPACE = re.compile(r"\s+")


def normalize_answer(text: str) -> str:
    out: list[str] = []
    for ch in unicodedata.normalize("NFKD", text):
        category = unicodedata.category(ch)
        if category == "Mn":                      # combining mark = diacritic
            continue
        if category == "Pd" or ch in "/\\":       # dashes and slashes separate words
            out.append(" ")
            continue
        if category.startswith("P"):              # other punctuation is dropped
            continue
        out.append(ch)
    return _WHITESPACE.sub(" ", "".join(out)).strip().casefold()


def is_correct(answer: str, accepted: Iterable[str]) -> bool:
    given = normalize_answer(answer)
    return given != "" and any(given == normalize_answer(a) for a in accepted)
