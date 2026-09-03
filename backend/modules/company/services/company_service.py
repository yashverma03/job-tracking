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


def is_covered_by_other_scraper(name: str | None, current_scraper_name: str | None) -> bool:
    """True when `name` belongs to a company that already has its own dedicated
    scraper, so an aggregator scraper (LinkedIn, Wellfound, ...) picking up the same
    company's listings would just create duplicates. Doesn't apply when the company's
    dedicated scraper is the one currently running - e.g. the Microsoft scraper must
    still be able to insert Microsoft jobs."""
    company = _get_company_by_name(name)
    if company is None or not company.has_scraper:
        return False
    return normalize_company_name(name) != normalize_company_name(current_scraper_name)
