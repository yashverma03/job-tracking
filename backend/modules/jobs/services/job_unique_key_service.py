from urllib.parse import urlsplit, urlunsplit

from modules.jobs.models import JobUniqueKey
from modules.jobs.utils.url_cleaner import clean_job_url


def normalize_for_dedup(url: str) -> str:
    cleaned = clean_job_url(url)
    parts = urlsplit(cleaned)
    path = parts.path.rstrip('/')
    return urlunsplit((parts.scheme, parts.netloc, path, '', ''))


def _normalized_keys(url: str | None, secondary_url: str | None) -> set[str]:
    return {normalize_for_dedup(value) for value in (url, secondary_url) if value}


def is_duplicate(url: str | None, secondary_url: str | None) -> bool:
    keys = _normalized_keys(url, secondary_url)
    if not keys:
        return False
    return JobUniqueKey.objects.filter(key__in=keys).exists()


def upsert_unique_keys(url: str | None, secondary_url: str | None) -> None:
    for key in _normalized_keys(url, secondary_url):
        JobUniqueKey.objects.get_or_create(key=key)


def mark_url_seen(url: str) -> str:
    key = normalize_for_dedup(url)
    JobUniqueKey.objects.get_or_create(key=key)
    return key


def normalize_company_official_key(company_name: str, official_id: str) -> str:
    return f'company:{company_name.strip().lower()}:id:{official_id.strip()}'


def upsert_company_official_key(company_name: str | None, official_id: str | None) -> None:
    if not company_name or not official_id:
        return
    key = normalize_company_official_key(company_name, official_id)
    JobUniqueKey.objects.get_or_create(key=key)
