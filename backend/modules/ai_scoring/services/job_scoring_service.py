from django_q.models import OrmQ
from django_q.tasks import async_task

from common.exceptions.api_exceptions import ApiError
from modules.ai_scoring.constants.ai_scoring_constants import JOB_SCORING_TASK_GROUP
from modules.jobs.enums.job_status import JobStatus
from modules.jobs.models import Job


def _eligible_jobs_queryset():
    return Job.objects.filter(deleted_at__isnull=True, status=JobStatus.PENDING)


def _batch_in_progress() -> bool:
   return OrmQ.objects.exists()


def trigger_job_scoring() -> dict:
    if _batch_in_progress():
        raise ApiError('A job scoring batch is already in progress.', status_code=409)

    job_ids = list(_eligible_jobs_queryset().values_list('id', flat=True))

    if not job_ids:
        return {'queued': False, 'processing': 0, 'message': 'No pending jobs to score.'}

    async_task(
        'modules.ai_scoring.tasks.run_job_scoring_batch_task',
        job_ids,
        group=JOB_SCORING_TASK_GROUP,
    )

    return {
        'queued': True,
        'processing': len(job_ids),
        'message': f'AI scoring queued for {len(job_ids)} job(s).',
    }
