import re
from dataclasses import dataclass

from common.utils.text_normalizer import normalize_text


@dataclass(frozen=True)
class TitleExclusionRule:
    """A single title-exclusion rule. Plain rules are matched as a normalized substring
    of the (normalized) incoming title; regex rules are matched with `re.search` against
    the normalized incoming title, and are not themselves normalized."""

    pattern: str
    is_regex: bool = False


# Roles that are out of scope regardless of scraper/source. Kept here (rather than per-scraper)
# so every strategy excludes the same set of titles.
EXCLUDED_TITLE_RULES: list[TitleExclusionRule] = [
    TitleExclusionRule('manager'),
    TitleExclusionRule('principle'),
    TitleExclusionRule('lead'),
    TitleExclusionRule('architect'),
    TitleExclusionRule('firmware'),
    TitleExclusionRule('sde 3'),
    TitleExclusionRule('sde 4'),
    TitleExclusionRule('staff'),
]

# Cities/regions in scope, matched as a normalized substring of the incoming location
# (each entry paired with its common alternate names/spellings).
ALLOWED_LOCATION_SUBSTRINGS: list[str] = [
    'delhi',
    'new delhi',
    'ncr',
    'national capital region',
    'gurgaon',
    'gurugram',
    'noida',
    'greater noida',
    'bangalore',
    'bengaluru',
    'hyderabad',
    'secunderabad',
    'pune',
    'chennai',
    'madras',
    'mumbai',
    'navi mumbai',
    'bombay',
    'remote',
]

# Only an exact "India" (no city specified) is in scope, not any location that merely
# contains "India" (e.g. "West Bengal, India").
EXACT_ALLOWED_LOCATIONS: list[str] = [
    'india',
]


def is_title_excluded(title: str | None) -> bool:
    normalized_title = normalize_text(title)
    if not normalized_title:
        return False

    for rule in EXCLUDED_TITLE_RULES:
        if rule.is_regex:
            if re.search(rule.pattern, normalized_title):
                return True
        elif normalize_text(rule.pattern) in normalized_title:
            return True

    return False


def is_location_excluded(location: str | None) -> bool:
    normalized_location = normalize_text(location)
    if not normalized_location:
        return False

    if normalized_location in EXACT_ALLOWED_LOCATIONS:
        return False

    return not any(normalize_text(city) in normalized_location for city in ALLOWED_LOCATION_SUBSTRINGS)
