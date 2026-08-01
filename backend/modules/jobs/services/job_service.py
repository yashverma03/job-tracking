from urllib.parse import urlsplit, urlunsplit

from django.db.models import Q
from django.utils import timezone

from common.exceptions.api_exceptions import ApiError
from common.types.pagination import PaginatedResult
from modules.jobs.models import Job
from modules.jobs.types.job_types import JobFilterParams
from modules.jobs.utils.url_cleaner import clean_job_url

SEARCH_FIELDS = ['url', 'title', 'company_name', 'official_id', 'description']


def _normalize_url(url: str) -> str:
    parts = urlsplit(url)
    path = parts.path.rstrip('/')
    return urlunsplit((parts.scheme, parts.netloc, path, '', ''))


def _ensure_url_not_duplicate(url: str | None) -> None:
    if not url:
        return

    normalized_url = _normalize_url(url)
    existing_urls = _active_jobs_queryset().filter(url__isnull=False).values_list('url', flat=True)
    if any(_normalize_url(existing_url) == normalized_url for existing_url in existing_urls):
        raise ApiError(
            'A job with this URL already exists.',
            status_code=400,
            details={'field': 'url'},
        )


def _active_jobs_queryset():
    return Job.objects.filter(deleted_at__isnull=True)


def _apply_filters(queryset, filters: JobFilterParams):
    if filters.status:
        queryset = queryset.filter(status=filters.status)
    if filters.referral_status:
        queryset = queryset.filter(referral_status=filters.referral_status)
    if filters.date_from:
        queryset = queryset.filter(created_at__date__gte=filters.date_from)
    if filters.date_to:
        queryset = queryset.filter(created_at__date__lte=filters.date_to)
    if filters.search:
        search_query = Q()
        for field in SEARCH_FIELDS:
            search_query |= Q(**{f'{field}__icontains': filters.search})
        queryset = queryset.filter(search_query)
    return queryset


def list_jobs(filters: JobFilterParams) -> PaginatedResult[Job]:
    queryset = _apply_filters(_active_jobs_queryset(), filters).order_by('-id')

    total = queryset.count()
    page = max(filters.page, 1)
    offset = (page - 1) * filters.limit
    items = list(queryset[offset:offset + filters.limit])

    return PaginatedResult(items=items, total=total, page=page, page_size=filters.limit)


def get_job(job_id: int) -> Job:
    job = _active_jobs_queryset().filter(id=job_id).first()
    if job is None:
        raise ApiError(f'Job {job_id} not found', status_code=404)
    return job


def create_job(data: dict) -> Job:
    if data.get('url'):
        data['url'] = clean_job_url(data['url'])
    _ensure_url_not_duplicate(data.get('url'))
    return Job.objects.create(**data)


def update_job(job_id: int, data: dict) -> Job:
    if data.get('url'):
        data['url'] = clean_job_url(data['url'])
    job = get_job(job_id)
    for field, value in data.items():
        setattr(job, field, value)
    job.save()
    return job


def soft_delete_job(job_id: int) -> None:
    job = get_job(job_id)
    job.deleted_at = timezone.now()
    job.save(update_fields=['deleted_at'])
