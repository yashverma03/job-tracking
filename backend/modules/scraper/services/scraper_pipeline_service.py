from django_q.models import Task
from django_q.tasks import async_task

from modules.scraper.scrapers.registry import get_enabled_scrapers
from modules.scraper.services import scraper_run_service
from modules.scraper.utils.scraper_logger import get_scraper_logger

SCRAPER_PIPELINE_TASK_GROUP = 'scraper_pipeline'


def run_pipeline() -> None:
    for scraper in get_enabled_scrapers():
        logger = get_scraper_logger(scraper.name)
        run = scraper_run_service.create_pending_run(scraper.name)
        logger.info('run started: run_id=%s', run.id)

        try:
            scraper_run_service.mark_processing(run)
            logger.info('run marked Processing')

            metadata = scraper.run()
            error_count = metadata.get('error_count', 0)

            if error_count:
                scraper_run_service.mark_failed(
                    run,
                    error={'message': f'{error_count} job(s) failed during the run.'},
                    metadata=metadata,
                )
                logger.error('run finished: Failed error_count=%s', error_count)
            else:
                scraper_run_service.mark_success(run, metadata=metadata)
                logger.info('run finished: Success')
        except Exception as exc:  # noqa: BLE001 - one scraper's failure must not abort remaining scrapers
            scraper_run_service.mark_failed(run, {'message': str(exc)})
            logger.error('run finished: Failed error=%s', exc)


def _pipeline_in_progress() -> bool:
    return Task.objects.filter(group=SCRAPER_PIPELINE_TASK_GROUP, stopped__isnull=True).exists()


def trigger_scraper_pipeline() -> dict:
    if _pipeline_in_progress():
        return {'queued': False, 'message': 'A scraper pipeline run is already in progress.'}

    async_task(
        'modules.scraper.tasks.run_scraper_pipeline_task',
        group=SCRAPER_PIPELINE_TASK_GROUP,
    )

    return {'queued': True, 'message': 'Scraper pipeline started.'}
