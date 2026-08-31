from collections import Counter

from django.db.models import Case, CharField, Count, IntegerField, Q, Value, When
from django.db.models.functions import Cast, Lower, Trim
from django.utils import timezone

from common.exceptions.api_exceptions import ApiError
from common.types.pagination import PaginatedResult
from modules.jobs.enums.job_referral_status import JobReferralStatus
from modules.jobs.enums.job_status import JobStatus
from modules.jobs.models import Job
from modules.jobs.services import job_unique_key_service
from modules.jobs.types.job_types import JobFilterParams
from modules.jobs.utils.domain import extract_domain, is_job_board_domain
from modules.jobs.utils.url_cleaner import clean_job_url

SEARCH_FIELDS = ['url', 'secondary_url', 'title', 'company_name', 'official_id']


def _ensure_url_not_duplicate(url: str | None, secondary_url: str | None) -> None:
    if job_unique_key_service.is_duplicate(url, secondary_url):
        raise ApiError(
            'A job with this URL already exists.',
            status_code=400,
            details={'field': 'url'},
        )


def _ensure_company_official_not_duplicate(company_name: str | None, official_id: str | None) -> None:
    if job_unique_key_service.is_company_official_duplicate(company_name, official_id):
        raise ApiError(
            'A job with this company and official ID already exists.',
            status_code=400,
            details={'field': 'official_id'},
        )


def _active_jobs_queryset():
    return Job.objects.filter(deleted_at__isnull=True)


def _apply_filters(queryset, filters: JobFilterParams):
    if filters.status:
        queryset = queryset.filter(status__in=filters.status)
    if filters.referral_status:
        queryset = queryset.filter(referral_status__in=filters.referral_status)
    if filters.date_from:
        queryset = queryset.filter(created_at__date__gte=filters.date_from)
    if filters.date_to:
        queryset = queryset.filter(created_at__date__lte=filters.date_to)
    if filters.search:
        queryset = queryset.annotate(id_str=Cast('id', output_field=CharField()))
        search_query = Q(id_str__icontains=filters.search)
        for field in SEARCH_FIELDS:
            search_query |= Q(**{f'{field}__icontains': filters.search})
        queryset = queryset.filter(search_query)
    if filters.is_custom_resume_generated is not None:
        queryset = queryset.filter(is_custom_resume_generated=filters.is_custom_resume_generated)
    if filters.has_description is not None:
        if filters.has_description:
            queryset = queryset.filter(description__isnull=False).exclude(description__exact='')
        else:
            queryset = queryset.filter(Q(description__isnull=True) | Q(description__exact=''))
    return queryset


def _with_default_sort_tier(queryset):
    return queryset.annotate(
        sort_tier=Case(
            When(status=JobStatus.TO_APPLY, then=Value(0)),
            When(referral_status=JobReferralStatus.REQUIRED, then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        )
    )


def list_jobs(filters: JobFilterParams) -> PaginatedResult[Job]:
    queryset = _with_default_sort_tier(_apply_filters(_active_jobs_queryset(), filters)).order_by(
        'sort_tier', 'company_name', '-id'
    )

    total = queryset.count()
    page = max(filters.page, 1)
    offset = (page - 1) * filters.limit
    items = list(queryset[offset:offset + filters.limit])

    return PaginatedResult(items=items, total=total, page=page, page_size=filters.limit)


def list_company_names(search: str | None = None, limit: int | None = None) -> list[str]:
    queryset = _active_jobs_queryset().exclude(company_name__isnull=True).exclude(company_name='')
    if search:
        queryset = queryset.filter(company_name__icontains=search)
    rows = queryset.values('company_name').annotate(count=Count('id')).order_by('-count', 'company_name')
    if limit is not None:
        rows = rows[:limit]
    return [row['company_name'] for row in rows]


def list_job_titles(search: str | None = None, limit: int | None = None) -> list[str]:
    queryset = _active_jobs_queryset().exclude(title__isnull=True).exclude(title='')
    if search:
        queryset = queryset.filter(title__icontains=search)
    rows = (
        queryset.annotate(normalized_title=Lower(Trim('title')))
        .values('normalized_title')
        .annotate(count=Count('id'))
        .filter(count__gte=10)
        .order_by('-count', 'normalized_title')
    )
    if limit is not None:
        rows = rows[:limit]
    return [row['normalized_title'].title() for row in rows]


def get_company_name_by_url(url: str) -> str | None:
    domain = extract_domain(url)
    if not domain or is_job_board_domain(domain):
        return None

    candidates = (
        _active_jobs_queryset()
        .exclude(url__isnull=True)
        .exclude(url='')
        .exclude(company_name__isnull=True)
        .exclude(company_name='')
        .values_list('url', 'company_name')
    )

    company_name_counts = Counter(
        company_name for candidate_url, company_name in candidates if extract_domain(candidate_url) == domain
    )
    if not company_name_counts:
        return None
    return max(company_name_counts.items(), key=lambda item: (item[1], item[0]))[0]


def get_job_stats() -> dict:
    queryset = _active_jobs_queryset()
    return {
        'to_apply_count': queryset.filter(status=JobStatus.TO_APPLY).count(),
        'referral_required_count': queryset.filter(referral_status=JobReferralStatus.REQUIRED).count(),
        'pending_jobs_count': queryset.filter(status=JobStatus.PENDING).count(),
    }


def get_job(job_id: int) -> Job:
    job = _active_jobs_queryset().filter(id=job_id).first()
    if job is None:
        raise ApiError(f'Job {job_id} not found', status_code=404)
    return job


def create_job(data: dict) -> Job:
    if data.get('url'):
        data['url'] = clean_job_url(data['url'])
    if data.get('secondary_url'):
        data['secondary_url'] = clean_job_url(data['secondary_url'])
    _ensure_url_not_duplicate(data.get('url'), data.get('secondary_url'))
    _ensure_company_official_not_duplicate(data.get('company_name'), data.get('official_id'))
    job = Job.objects.create(**data)
    job_unique_key_service.upsert_unique_keys(job.url, job.secondary_url)
    job_unique_key_service.upsert_company_official_key(job.company_name, job.official_id)
    return job


def create_scraped_job(
    title: str | None,
    company_name: str | None,
    location: str | None,
    description: str | None,
    url: str,
    referral_status: str,
    official_id: str | None = None,
    status: str = JobStatus.PENDING,
) -> Job:
    return create_job(
        {
            'title': title,
            'company_name': company_name,
            'location': location,
            'description': description,
            'url': url,
            'status': status,
            'is_manual_created': False,
            'referral_status': referral_status,
            'official_id': official_id,
        }
    )


def update_job(job_id: int, data: dict) -> Job:
    if data.get('url'):
        data['url'] = clean_job_url(data['url'])
    if data.get('secondary_url'):
        data['secondary_url'] = clean_job_url(data['secondary_url'])
    job = get_job(job_id)

    for field, value in data.items():
        setattr(job, field, value)
    job.save()
    job_unique_key_service.upsert_unique_keys(job.url, job.secondary_url)
    job_unique_key_service.upsert_company_official_key(job.company_name, job.official_id)
    return job


def update_job_score(job_id: int, score: int, analysis: str) -> Job:
    job = get_job(job_id)
    job.score = score
    job.analysis = analysis
    update_fields = ['score', 'analysis']

    if job.status in (JobStatus.PENDING, JobStatus.TO_APPLY, JobStatus.NOT_RELEVANT):
        job.status = JobStatus.TO_APPLY if score == 100 else JobStatus.NOT_RELEVANT
        update_fields.append('status')

    job.save(update_fields=update_fields)
    return job


def mark_url_seen(url: str) -> str:
    cleaned_url = clean_job_url(url)
    return job_unique_key_service.mark_url_seen(cleaned_url)


def soft_delete_job(job_id: int) -> None:
    job = get_job(job_id)
    job.deleted_at = timezone.now()
    job.save(update_fields=['deleted_at'])
