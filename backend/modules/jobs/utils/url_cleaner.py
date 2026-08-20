import re

# Matches the numeric job id after "currentJobId=" (collection/search URLs) or
# "jobs/view/" (plain "jobs/view/<id>" or slug form "jobs/view/some-title-<id>").
# The slug can contain percent-encoded characters (e.g. "c%23-engineer"), so we
# skip any non-separator chars up to the trailing digit run instead of relying
# on a strict [\w-]* prefix.
LINKEDIN_JOB_ID_PATTERN = re.compile(r'currentJobId=(\d+)|jobs/view/[^?&]*?(\d+)(?=[/?&]|$)')


def extract_linkedin_job_id(url: str) -> str | None:
    match = LINKEDIN_JOB_ID_PATTERN.search(url)
    if not match:
        return None
    return match.group(1) or match.group(2)


def _clean_linkedin_url(url: str) -> str:
    job_id = extract_linkedin_job_id(url)
    return f'https://www.linkedin.com/jobs/view/{job_id}' if job_id else url


def clean_job_url(url: str) -> str:
    trimmed = url.strip()
    if 'linkedin.com' in trimmed:
        return _clean_linkedin_url(trimmed)
    return trimmed
