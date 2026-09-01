import re

_NON_ALNUM_PATTERN = re.compile(r'[^a-z0-9]+')


def normalize_text(value: str | None, delimiter: str = '') -> str:
    """Lowercase and replace all non-alphanumeric characters with `delimiter` (default: remove
    them, no spaces inserted in their place). Standard baseline normalization shared by any code
    that needs to compare free-text strings (titles, locations, names) loosely rather than
    exactly."""
    if not value:
        return ''
    return _NON_ALNUM_PATTERN.sub(delimiter, value.lower())
