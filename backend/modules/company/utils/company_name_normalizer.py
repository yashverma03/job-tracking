import re

from common.utils.text_normalizer import normalize_text

# Legal-entity suffixes and India-specific qualifiers that vary between listings of the
# same company (e.g. "Acme India", "Acme Pvt Ltd", "Acme Private Limited") but shouldn't
# stop them from being treated as the same company. Matched after normalize_text has
# already lowercased and removed all non-alphanumeric characters (no spaces), so these
# patterns are written the same way - as contiguous alphanumeric runs, not phrases.
_SUFFIX_PATTERN = re.compile(
    r'('
    r'forindia|inindia|india|'
    r'pvtltd|privatelimited|pvt|'
    r'ltd|limited|'
    r'llp|llc|incorporated|inc|'
    r'corporation|corp|'
    r'gmbh|plc'
    r')$'
)


def normalize_company_name(name: str | None) -> str:
    """Normalize a company name for matching purposes: apply the standard text
    normalization, then strip a trailing legal-entity/country suffix.
    E.g. "Acme Technologies (India) Pvt. Ltd." -> "acmetechnologies"."""
    if not name:
        return ''

    normalized = normalize_text(name)
    while True:
        stripped = _SUFFIX_PATTERN.sub('', normalized)
        if stripped == normalized:
            return stripped
        normalized = stripped
