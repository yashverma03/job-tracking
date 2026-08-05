from urllib.parse import urlparse

JOB_BOARD_DOMAINS = {
    'linkedin.com',
    'indeed.com',
    'naukri.com',
    'glassdoor.com',
    'cutshort.io',
    'instahyre.com',
    'monster.com',
    'ziprecruiter.com',
    'angel.co',
    'wellfound.com',
    'dice.com',
    'simplyhired.com',
    'ycombinator.com',
    'ashbyhq.com',
    'greenhouse.io',
    'lever.co',
    'workable.com',
    'smartrecruiters.com',
    'icims.com',
    'jobvite.com',
    'bamboohr.com',
    'breezy.hr',
    'builtin.com',
}


def extract_domain(url: str) -> str | None:
    trimmed = url.strip()
    if not trimmed:
        return None
    if '://' not in trimmed:
        trimmed = f'https://{trimmed}'
    hostname = urlparse(trimmed).hostname
    if not hostname:
        return None
    return hostname[4:] if hostname.startswith('www.') else hostname


def is_job_board_domain(domain: str) -> bool:
    return any(domain == board or domain.endswith(f'.{board}') for board in JOB_BOARD_DOMAINS)
