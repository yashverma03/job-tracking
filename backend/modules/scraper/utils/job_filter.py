from common.utils.text_normalizer import normalize_text

# Roles that are out of scope regardless of scraper/source. Kept here (rather than per-scraper)
# so every strategy excludes the same set of titles. A title is excluded if any of these
# words/phrases is present anywhere in it, after normalizing both sides.
EXCLUDED_TITLE_WORDS: list[str] = [
    'manager',
    'principle',
    'lead',
    'architect',
    'firmware',
    'sde 3',
    'sde 4',
    'sde iii',
    'sde iv',
    'staff',
    '.net developer',
    'golang developer',
    'c# developer',
    'c# engineer',
    'qa engineer',
    'sdet',
    'test',
    'embedded',
    'consultant',
    'scala',
    'mulesoft',
    'salesforce',
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

    return any(normalize_text(word) in normalized_title for word in EXCLUDED_TITLE_WORDS)


def is_location_excluded(location: str | None) -> bool:
    normalized_location = normalize_text(location)
    if not normalized_location:
        return False

    if normalized_location in EXACT_ALLOWED_LOCATIONS:
        return False

    return not any(normalize_text(city) in normalized_location for city in ALLOWED_LOCATION_SUBSTRINGS)
