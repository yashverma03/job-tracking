import re
from urllib.parse import urlunsplit, urlsplit

LINKEDIN_JOB_ID_PATTERN = re.compile(r'(?:currentJobId=|jobs/view/)(\d+)')


def _strip_hash(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ''))


def _extract_linkedin_job_id(url: str) -> str | None:
    match = LINKEDIN_JOB_ID_PATTERN.search(url)
    return match.group(1) if match else None


def _clean_linkedin_url(url: str) -> str:
    job_id = _extract_linkedin_job_id(url)
    return f'https://www.linkedin.com/jobs/view/{job_id}' if job_id else _strip_hash(url)


def clean_job_url(url: str) -> str:
    trimmed = url.strip()
    if 'linkedin.com' in trimmed:
        return _clean_linkedin_url(trimmed)
    return _strip_hash(trimmed)
