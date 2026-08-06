from datetime import timedelta

from django.utils import timezone

from modules.jobs.models import JobUniqueKey

DUPLICATE_LOOKBACK_DAYS = 182  # ~6 months


def _keys(url: str | None, secondary_url: str | None) -> set[str]:
    return {value for value in (url, secondary_url) if value}


def _lookback_cutoff():
    return timezone.now() - timedelta(days=DUPLICATE_LOOKBACK_DAYS)


def is_duplicate(url: str | None, secondary_url: str | None) -> bool:
    keys = _keys(url, secondary_url)
    if not keys:
        return False
    return JobUniqueKey.objects.filter(key__in=keys, updated_at__gte=_lookback_cutoff()).exists()


def upsert_unique_keys(url: str | None, secondary_url: str | None) -> None:
    for key in _keys(url, secondary_url):
        JobUniqueKey.objects.update_or_create(key=key, defaults={'updated_at': timezone.now()})


def mark_url_seen(url: str) -> str:
    JobUniqueKey.objects.get_or_create(key=url)
    return url


def normalize_company_official_key(company_name: str, official_id: str) -> str:
    return f'company:{company_name.strip().lower()}:id:{official_id.strip()}'


def is_company_official_duplicate(company_name: str | None, official_id: str | None) -> bool:
    if not company_name or not official_id:
        return False
    if not company_name.strip() or not official_id.strip():
        return False
    key = normalize_company_official_key(company_name, official_id)
    return JobUniqueKey.objects.filter(key=key, updated_at__gte=_lookback_cutoff()).exists()


def upsert_company_official_key(company_name: str | None, official_id: str | None) -> None:
    if not company_name or not official_id:
        return
    if not company_name.strip() or not official_id.strip():
        return
    key = normalize_company_official_key(company_name, official_id)
    JobUniqueKey.objects.update_or_create(key=key, defaults={'updated_at': timezone.now()})
