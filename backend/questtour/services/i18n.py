type I18nDict = dict[str, str] | None


def pick_text(base: str, i18n: I18nDict, lang: str) -> str:
    """Return the translation for `lang` if present and non-empty, otherwise `base`."""
    if not i18n:
        return base
    value = i18n.get(lang)
    if value is None or value.strip() == "":
        return base
    return value
