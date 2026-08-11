import os
import threading

from django import db

from common.exceptions.api_exceptions import ApiError
from common.utils.env import get_env
from common.utils.notification_manager import NotificationManager
from modules.jobs.enums.job_status import JobStatus
from modules.jobs.models import Job
from modules.resume.services.resume_ai_service import generate_resume_content
from modules.resume.services.resume_pdf_service import render_resume_pdf
from modules.resume.types.resume_types import ResumeGenerationOutcome, ResumeInput
from modules.resume.utils.resume_input_loader import load_resume_input
from modules.resume.utils.resume_log import log_resume_batch_result, log_resume_progress

_batch_lock = threading.Lock()


def _resume_filename(resume_input: ResumeInput, job_id: int) -> str:
    name_slug = '_'.join(word.capitalize() for word in resume_input.contact.name.split())
    return f'{name_slug}_Resume_{job_id}.pdf'


def _eligible_jobs_queryset():
    return Job.objects.filter(
        deleted_at__isnull=True,
        status=JobStatus.TO_APPLY,
        is_custom_resume_generated=False,
    )


def _process_job(job: Job, resume_input: ResumeInput, output_dir: str) -> ResumeGenerationOutcome:
    if not job.description or not job.description.strip():
        return ResumeGenerationOutcome(
            job_id=job.pk,
            error='Job description is required to generate a resume.',
        )

    try:
        ai_output = generate_resume_content(job.title or '', job.description or '', resume_input)
        file_path = os.path.join(output_dir, _resume_filename(resume_input, job.pk))
        render_resume_pdf(resume_input, ai_output, file_path)

        job.is_custom_resume_generated = True
        job.save(update_fields=['is_custom_resume_generated'])

        return ResumeGenerationOutcome(job_id=job.pk, file_path=file_path)
    except Exception as exc:  # noqa: BLE001 - one job's failure must not abort the batch
        return ResumeGenerationOutcome(job_id=job.pk, error=str(exc))


def _run_batch(jobs: list[Job], resume_input: ResumeInput, output_dir: str) -> None:
    try:
        outcomes = []
        for index, job in enumerate(jobs, start=1):
            outcome = _process_job(job, resume_input, output_dir)
            outcomes.append(outcome)
            log_resume_progress(index, len(jobs), outcome)

        generated = [outcome for outcome in outcomes if outcome.file_path is not None]
        failed = [outcome for outcome in outcomes if outcome.file_path is None]

        log_resume_batch_result(total=len(jobs), generated=generated, failed=failed)
        NotificationManager.show(
            'Resume generation complete',
            f'Total: {len(jobs)}\nSuccess: {len(generated)}\nFailed: {len(failed)}',
        )
    finally:
        db.connections.close_all()
        _batch_lock.release()


def generate_resumes_for_pending_jobs() -> dict:
    if not _batch_lock.acquire(blocking=False):
        return {'queued': False, 'processing': 0, 'message': 'A resume generation batch is already in progress.'}

    started = False
    try:
        resume_input = load_resume_input()
        output_dir = get_env('RESUME_OUTPUT_DIR')
        jobs = list(_eligible_jobs_queryset())

        if not jobs:
            return {'queued': False, 'processing': 0, 'message': 'No jobs pending resume generation.'}

        thread = threading.Thread(target=_run_batch, args=(jobs, resume_input, output_dir), daemon=True)
        thread.start()
        started = True

        return {
            'queued': True,
            'processing': len(jobs),
            'message': f'Resume generation queued for {len(jobs)} job(s).',
        }
    finally:
        if not started:
            _batch_lock.release()


def generate_resume_for_job(job_id: int) -> ResumeGenerationOutcome:
    job = Job.objects.filter(deleted_at__isnull=True, id=job_id).first()
    if job is None:
        raise ApiError(f'Job {job_id} not found', status_code=404)

    resume_input = load_resume_input()
    output_dir = get_env('RESUME_OUTPUT_DIR')

    return _process_job(job, resume_input, output_dir)
