from datetime import datetime

from common.exceptions.api_exceptions import ApiError
from common.utils.notification_manager import NotificationManager
from modules.ai.constants.ai_constants import CLAUDE_LOG_PATH
from modules.ai.services.job_scoring_ai_service import score_job
from modules.ai_scoring.constants.ai_scoring_constants import SCORE_THRESHOLD
from modules.ai_scoring.types.job_scoring_types import JobScoringOutcome
from modules.jobs.enums.job_status import JobStatus
from modules.jobs.models import Job


def _log(message: str) -> None:
    timestamp = datetime.now().isoformat(sep=' ', timespec='seconds')
    with open(CLAUDE_LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(f'[{timestamp}] [job-scoring] {message}\n')


def _process_job(job: Job) -> JobScoringOutcome:
    try:
        outcome = score_job(job.pk, job.company_name or '', job.title or '', job.description or '', job.location or '')
        score = outcome.score
        if score is None:
            raise ApiError('AI scoring response did not include a score.', status_code=500)

        job.score = score
        job.analysis = outcome.analysis
        job.status = JobStatus.APPLIED if score >= SCORE_THRESHOLD else JobStatus.NOT_RELEVANT
        job.save(update_fields=['score', 'analysis', 'status'])

        return outcome
    except Exception as exc:  # noqa: BLE001 - one job's failure must not abort the batch
        return JobScoringOutcome(job_id=job.pk, error=str(exc))


def run_job_scoring_batch_task(job_ids: list[int]) -> None:
    jobs = list(Job.objects.filter(id__in=job_ids, deleted_at__isnull=True))

    outcomes = []
    for index, job in enumerate(jobs, start=1):
        outcome = _process_job(job)
        outcomes.append(outcome)
        _log(f'job {index} of {len(jobs)} done — job_id={outcome.job_id} '
             f'status={"success" if outcome.error is None else "failed"} '
             f'detail={outcome.score if outcome.error is None else outcome.error}')

    scored = [outcome for outcome in outcomes if outcome.error is None]
    failed = [outcome for outcome in outcomes if outcome.error is not None]

    _log(f'BATCH SUMMARY total={len(jobs)} success={len(scored)} failed={len(failed)}')
    NotificationManager.show(
        'AI job scoring complete',
        f'Total: {len(jobs)}\nSuccess: {len(scored)}\nFailed: {len(failed)}',
    )
