from django_q.tasks import async_task

from common.utils.env import get_env_int
from common.utils.notification_manager import NotificationManager
from modules.scraper.base.base_scraper import BaseScraper
from modules.scraper.models import ScraperRun
from modules.scraper.scrapers.registry import get_enabled_scrapers
from modules.scraper.services import scraper_run_service
from modules.scraper.utils.scraper_logger import get_scraper_logger

SCRAPER_PIPELINE_TASK_GROUP = 'scraper_pipeline'

MAX_JOBS_PER_RUN_ENV_KEY = 'SCRAPER_MAX_JOBS_PER_RUN'
START_OFFSET_ENV_KEY = 'SCRAPER_START_OFFSET'
TIME_RANGE_HOURS_ENV_KEY = 'SCRAPER_TIME_RANGE_HOURS'

SUMMARY_NOTIFICATION_WIDTH = 520
SUMMARY_NOTIFICATION_HEIGHT = 320


def run_scraper(scraper: BaseScraper, max_jobs_per_run: int, start_offset: int, time_range_hours: int) -> None:
    """Run a single scraper end-to-end (its own run record and status transitions).
    Queued as one Django-Q task per scraper so that scrapers execute in parallel across
    worker processes instead of one after another. Once the last scraper in the batch
    finishes, a single summary notification for the whole batch is shown (see
    `_notify_if_pipeline_complete`)."""
    logger = get_scraper_logger(scraper.name)
    run = scraper_run_service.create_pending_run(scraper.name)
    logger.info('run started: run_id=%s', run.id)

    try:
        scraper_run_service.mark_processing(run)
        logger.info('run marked Processing')

        result = scraper.run(max_jobs_per_run, start_offset, time_range_hours)
        metadata = result.metadata
        errors = result.errors

        if errors:
            scraper_run_service.mark_failed(
                run,
                error={'message': f'{len(errors)} job(s) failed during the run.', 'errors': errors},
                metadata=metadata,
            )
            logger.error('run finished: Failed error_count=%s', len(errors))
        else:
            scraper_run_service.mark_success(run, metadata=metadata)
            logger.info('run finished: Success')
    except Exception as exc:  # noqa: BLE001 - one scraper's failure must not abort others
        scraper_run_service.mark_failed(run, {'message': str(exc)})
        logger.error('run finished: Failed error=%s', exc)

    _notify_if_pipeline_complete()


def _run_counts(run: ScraperRun) -> tuple[int, int]:
    metadata = run.metadata or {}
    error_count = metadata.get('error_count', 0)
    success_count = max(metadata.get('total_unique_count', 0) - error_count, 0)
    return success_count, error_count


def _build_summary_message(runs: list[ScraperRun]) -> str:
    header = f'{"Scraper":<18}{"Status":<12}{"Success":>8}{"Failed":>8}'
    rows = [header, '-' * len(header)]

    for run in runs:
        success_count, error_count = _run_counts(run)
        rows.append(f'{run.name:<18}{run.status:<12}{success_count:>8}{error_count:>8}')

    # wrap in <tt> so zenity's pango markup renders the columns in a monospace font
    return '<tt>' + '\n'.join(rows) + '</tt>'


def _notify_if_pipeline_complete() -> None:
    """Every scraper task calls this when it finishes; only the task that finds no
    other Pending/Processing runs left (i.e. the last one to complete) actually shows
    the batch summary notification."""
    if scraper_run_service.has_run_in_progress():
        return

    runs = scraper_run_service.get_runs_for_today()
    if not runs:
        return

    NotificationManager.show(
        'Scraper pipeline complete',
        _build_summary_message(runs),
        width=SUMMARY_NOTIFICATION_WIDTH,
        height=SUMMARY_NOTIFICATION_HEIGHT,
    )


def _pipeline_in_progress() -> bool:
    return scraper_run_service.has_run_in_progress()


def trigger_scraper_pipeline() -> dict:
    if _pipeline_in_progress():
        return {'queued': False, 'message': 'A scraper pipeline run is already in progress.'}

    max_jobs_per_run = get_env_int(MAX_JOBS_PER_RUN_ENV_KEY)
    start_offset = get_env_int(START_OFFSET_ENV_KEY)
    time_range_hours = get_env_int(TIME_RANGE_HOURS_ENV_KEY)

    for scraper in get_enabled_scrapers():
        async_task(
            'modules.scraper.tasks.run_scraper_task',
            scraper.name,
            max_jobs_per_run,
            start_offset,
            time_range_hours,
            group=SCRAPER_PIPELINE_TASK_GROUP,
        )

    return {'queued': True, 'message': 'Scraper pipeline started.'}


def init_scraper_pipeline() -> dict:
    if scraper_run_service.has_run_today():
        return {'queued': False, 'message': 'A scraper pipeline run already exists for today.'}

    return trigger_scraper_pipeline()
