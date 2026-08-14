from django_q.models import Task
from django_q.tasks import async_task

from modules.jobs.enums.job_status import JobStatus
from modules.jobs.services import job_service
from modules.scraper.scrapers.registry import get_enabled_scrapers
from modules.scraper.services import scraper_run_service
from modules.scraper.utils.scraper_logger import get_scraper_logger

SCRAPER_PIPELINE_TASK_GROUP = 'scraper_pipeline'


def _insert_scraped_job(job_data) -> None:
    job_service.create_job(
        {
            'title': job_data.title,
            'company_name': job_data.company_name,
            'location': job_data.location,
            'description': job_data.description,
            'url': job_data.url,
            'status': JobStatus.PENDING,
            'is_manual_created': False,
        }
    )


def run_pipeline() -> None:
    for scraper in get_enabled_scrapers():
        logger = get_scraper_logger(scraper.name)
        run = scraper_run_service.create_pending_run(scraper.name)
        logger.info('run started: run_id=%s', run.id)

        try:
            scraper_run_service.mark_processing(run)
            logger.info('run marked Processing')

            jobs = scraper.get_data()
            logger.info('get_data returned %s job(s)', len(jobs))

            for job_data in jobs:
                try:
                    _insert_scraped_job(job_data)
                    logger.info('job inserted: %s', job_data.url)
                except Exception as exc:  # noqa: BLE001 - one job's failure must not abort the run
                    logger.warning('job insert failed for %s: %s', job_data.url, exc)

            scraper_run_service.mark_success(run, metadata=scraper.get_last_run_metadata())
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
