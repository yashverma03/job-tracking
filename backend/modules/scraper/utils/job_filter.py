from common.utils.text_normalizer import normalize_text

# Roles that are out of scope regardless of scraper/source. Kept here (rather than per-scraper)
# so every strategy excludes the same set of titles. A title is excluded if any of these
# words/phrases is present anywhere in it, after normalizing both sides.
EXCLUDED_TITLE_WORDS: list[str] = [
    'manager',
    'principle',
    'principal',
    'lead',
    'architect',
    'firmware',
    'sde 3',
    'sde 4',
    'sde iii',
    'sde iv',
    'sde 3 developer',
    'sde 3 engineer',
    'sde 4 developer',
    'sde 4 engineer',
    'sde iii developer',
    'sde iii engineer',
    'sde iv developer',
    'sde iv engineer',
    'software development engineer 3',
    'software development engineer 4',
    'software development engineer iii',
    'software development engineer iv',
    'software developer 3',
    'software developer 4',
    'software developer iii',
    'software developer iv',
    'software engineer 3',
    'software engineer 4',
    'software engineer iii',
    'software engineer iv',
    'staff',
    '.net developer',
    '.net',
    'asp.net',
    'golang developer',
    'golang',
    'go developer',
    'c# developer',
    'c# engineer',
    'c++ developer',
    'c++ engineer',
    'rust',
    'ruby on rails',
    'ruby developer',
    'php',
    'laravel',
    'qa engineer',
    'qa',
    'sdet',
    'test',
    'embedded',
    'consultant',
    'consulting',
    'scala developer',
    'scala engineer',
    'mulesoft',
    'intern',
    'support engineer',
    'support developer',
    'customer engineer',
    'hardware',
    'cyber security',
    'blockchain',
    'ai research',
    'data scientist',
    'data analyst',
    'ml engineer',
    'devops engineer',
    'cloud engineer',
    'forward deployed',
    'solutions engineer',
    'founding engineer',
    'cto',
    'distinguished engineer',
    'associate vp',
    'vice president',
    'junior',
    'director',
    'leader',
    'leadership',
    'tester',
    'testing',
    'internship',
    'instructor',
    'teaching',
    'trainer',
    'Network Developer',
    'Network Engineer',
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
    'location'
]

# Only an exact "India" (no city specified) is in scope, not any location that merely
# contains "India" (e.g. "West Bengal, India").
EXACT_ALLOWED_LOCATIONS: list[str] = [
    'india',
]


def is_title_excluded(title: str | None) -> bool:
    if not title:
        return False

    normalized_title = normalize_text(title, ' ').strip()
    if not normalized_title:
        return False

    title_words = normalized_title.split(' ')

    for word in EXCLUDED_TITLE_WORDS:
        normalized_word = word.lower().strip()
        if len(normalized_word) == 1:
            if normalized_word in title_words:
                return True
        elif normalized_word in normalized_title:
            return True

    return False


def is_location_excluded(location: str | None) -> bool:
    normalized_location = normalize_text(location)
    if not normalized_location:
        return False

    if normalized_location in EXACT_ALLOWED_LOCATIONS:
        return False

    return not any(normalize_text(city) in normalized_location for city in ALLOWED_LOCATION_SUBSTRINGS)
