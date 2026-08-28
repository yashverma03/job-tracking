from django.utils import timezone

from modules.company.enums.company_type import CompanyType
from modules.company.models import Company
from modules.company.utils import normalize_company_name


def _active_companies_queryset():
    return Company.objects.filter(deleted_at__isnull=True)


def _get_company_by_name(name: str | None) -> Company | None:
    normalized_name = normalize_company_name(name)
    if not normalized_name:
        return None

    for company in _active_companies_queryset():
        if normalize_company_name(company.name) == normalized_name:
            return company
    return None


def is_blacklisted(name: str | None) -> bool:
    company = _get_company_by_name(name)
    return company is not None and company.type == CompanyType.BLACKLIST


def is_top_company(name: str | None) -> bool:
    company = _get_company_by_name(name)
    return company is not None and company.type == CompanyType.TOP_COMPANY


def is_in_cooling_period(name: str | None) -> bool:
    company = _get_company_by_name(name)
    return (
        company is not None
        and company.cooling_period_end_at is not None
        and company.cooling_period_end_at > timezone.now()
    )
