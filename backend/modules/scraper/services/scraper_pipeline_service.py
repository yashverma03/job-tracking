from django_q.tasks import async_task

from common.utils.notification_manager import NotificationManager
from modules.scraper.scrapers.registry import get_enabled_scrapers
from modules.scraper.services import scraper_run_service
from modules.scraper.utils.scraper_logger import get_scraper_logger

SCRAPER_PIPELINE_TASK_GROUP = 'scraper_pipeline'


def run_pipeline(max_jobs_per_run: int, start_offset: int) -> None:
    succeeded = []
    failed = []

    for scraper in get_enabled_scrapers():
        logger = get_scraper_logger(scraper.name)
        run = scraper_run_service.create_pending_run(scraper.name)
        logger.info('run started: run_id=%s', run.id)

        try:
            scraper_run_service.mark_processing(run)
            logger.info('run marked Processing')

            result = scraper.run(max_jobs_per_run, start_offset)
            metadata = result.metadata
            errors = result.errors

            if errors:
                scraper_run_service.mark_failed(
                    run,
                    error={'message': f'{len(errors)} job(s) failed during the run.', 'errors': errors},
                    metadata=metadata,
                )
                logger.error('run finished: Failed error_count=%s', len(errors))
                failed.append(scraper.name)
            else:
                scraper_run_service.mark_success(run, metadata=metadata)
                logger.info('run finished: Success')
                succeeded.append(scraper.name)
        except Exception as exc:  # noqa: BLE001 - one scraper's failure must not abort remaining scrapers
            scraper_run_service.mark_failed(run, {'message': str(exc)})
            logger.error('run finished: Failed error=%s', exc)
            failed.append(scraper.name)

    NotificationManager.show(
        'Scraper pipeline complete',
        f'Total: {len(succeeded) + len(failed)}\nSuccess: {len(succeeded)}\nFailed: {len(failed)}',
    )


def _pipeline_in_progress() -> bool:
    return scraper_run_service.has_run_in_progress()


def trigger_scraper_pipeline(max_jobs_per_run: int, start_offset: int) -> dict:
    if _pipeline_in_progress():
        return {'queued': False, 'message': 'A scraper pipeline run is already in progress.'}

    async_task(
        'modules.scraper.tasks.run_scraper_pipeline_task',
        max_jobs_per_run,
        start_offset,
        group=SCRAPER_PIPELINE_TASK_GROUP,
    )

    return {'queued': True, 'message': 'Scraper pipeline started.'}


def init_scraper_pipeline(max_jobs_per_run: int, start_offset: int) -> dict:
    if scraper_run_service.has_run_today():
        return {'queued': False, 'message': 'A scraper pipeline run already exists for today.'}

    return trigger_scraper_pipeline(max_jobs_per_run, start_offset)
