from datetime import timedelta

from django.utils import timezone
from django_q.models import Schedule
from django_q.tasks import async_task, schedule

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

# Give any run that was recorded slightly late (e.g. a scraper that gets picked up by a
# worker a moment after the "last" task finishes) a chance to land in the DB before the
# batch summary is read, so the notification reflects the fully-resolved state.
NOTIFICATION_DELAY = timedelta(minutes=1)
NOTIFY_PIPELINE_COMPLETE_TASK = 'modules.scraper.tasks.notify_pipeline_complete_task'


def run_scraper(scraper: BaseScraper, max_jobs_per_run: int, start_offset: int, time_range_hours: int) -> None:
    """Run a single scraper end-to-end (its own run record and status transitions).
    Queued as one Django-Q task per scraper so that scrapers execute in parallel across
    worker processes instead of one after another. Once the last scraper in the batch
    finishes, a single summary notification for the whole batch is shown (see
    `_notify_if_pipeline_complete`).

    Idempotent per scraper per day: if this scraper already has a run recorded for
    today, it's skipped - re-triggering the pipeline (e.g. clicking the button again)
    only picks up scrapers that haven't run yet today."""
    logger = get_scraper_logger(scraper.name)

    if scraper_run_service.has_run_today_for_scraper(scraper.name):
        logger.info('skipping run, already ran today')
        _notify_if_pipeline_complete()
        return

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

    total_new_jobs = 0
    for run in runs:
        success_count, error_count = _run_counts(run)
        total_new_jobs += success_count
        rows.append(f'{run.name:<18}{run.status:<12}{success_count:>8}{error_count:>8}')

    rows.append('-' * len(header))
    rows.append(f'Total new jobs: {total_new_jobs}')

    # wrap in <tt> so zenity's pango markup renders the columns in a monospace font
    return '<tt>' + '\n'.join(rows) + '</tt>'


def _notify_if_pipeline_complete() -> None:
    """Every scraper task calls this when it finishes; only the task that finds no
    other Pending/Processing runs left (i.e. the last one to complete) actually schedules
    the batch summary notification. The notification itself is delayed (see
    `check_and_notify_pipeline_complete`) so a run that gets recorded a moment after the
    "last" task finishes still has time to land before the summary is read."""
    if scraper_run_service.has_run_in_progress():
        return

    # Avoid scheduling duplicate notifications if more than one task observes an empty
    # in-progress queue in quick succession.
    if Schedule.objects.filter(func=NOTIFY_PIPELINE_COMPLETE_TASK, next_run__gte=timezone.now()).exists():
        return

    schedule(
        NOTIFY_PIPELINE_COMPLETE_TASK,
        schedule_type=Schedule.ONCE,
        next_run=timezone.now() + NOTIFICATION_DELAY,
    )


def check_and_notify_pipeline_complete() -> None:
    """Runs once, `NOTIFICATION_DELAY` after the pipeline appeared complete. Re-checks
    that nothing is in progress (in case a new run started in the meantime) before
    showing the summary notification for today's runs."""
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


def trigger_scraper_pipeline() -> dict:
    if scraper_run_service.has_run_in_progress():
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
