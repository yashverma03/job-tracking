import re

_NON_ALNUM_PATTERN = re.compile(r'[^a-z0-9]+')


def normalize_text(value: str | None) -> str:
    """Lowercase and remove all non-alphanumeric characters (no spaces inserted in their
    place). Standard baseline normalization shared by any code that needs to compare
    free-text strings (titles, locations, names) loosely rather than exactly."""
    if not value:
        return ''
    return _NON_ALNUM_PATTERN.sub('', value.lower())
