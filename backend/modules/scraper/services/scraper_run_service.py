from django.utils import timezone

from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.enums.scraper_run_status import ScraperRunStatus
from modules.scraper.models import ScraperRun


def create_pending_run(name: ScraperName) -> ScraperRun:
    return ScraperRun.objects.create(name=name, status=ScraperRunStatus.PENDING)


def has_run_in_progress() -> bool:
    return ScraperRun.objects.filter(
        status__in=[ScraperRunStatus.PENDING, ScraperRunStatus.PROCESSING]
    ).exists()


def has_run_today() -> bool:
    return ScraperRun.objects.filter(created_at__date=timezone.now().date()).exists()


def has_run_today_for_scraper(name: ScraperName) -> bool:
    return ScraperRun.objects.filter(name=name, created_at__date=timezone.now().date()).exists()


def get_runs_for_today() -> list[ScraperRun]:
    return list(
        ScraperRun.objects.filter(created_at__date=timezone.now().date()).order_by('name', 'created_at')
    )


def count_runs_in_progress_today() -> int:
    return ScraperRun.objects.filter(
        status__in=[ScraperRunStatus.PENDING, ScraperRunStatus.PROCESSING],
        created_at__date=timezone.now().date(),
    ).count()


def mark_processing(run: ScraperRun) -> None:
    run.status = ScraperRunStatus.PROCESSING
    run.save(update_fields=['status'])


def mark_success(run: ScraperRun, metadata: dict | None = None) -> None:
    run.status = ScraperRunStatus.SUCCESS
    run.metadata = metadata
    run.completed_at = timezone.now()
    run.save(update_fields=['status', 'metadata', 'completed_at'])


def mark_failed(run: ScraperRun, error: dict, metadata: dict | None = None) -> None:
    run.status = ScraperRunStatus.FAILED
    run.error = error
    run.metadata = metadata
    run.completed_at = timezone.now()
    run.save(update_fields=['status', 'error', 'metadata', 'completed_at'])
