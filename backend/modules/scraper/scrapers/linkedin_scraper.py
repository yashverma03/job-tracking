import random
import secrets

from bs4 import BeautifulSoup
from curl_cffi import requests

from common.utils.env import get_env, get_env_int
from modules.jobs.services import job_service, job_unique_key_service
from modules.jobs.utils.url_cleaner import clean_job_url, extract_linkedin_job_id
from modules.scraper.base.base_scraper import BaseScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.types import ScraperRunResult
from modules.scraper.utils.rate_limiter import wait_between_requests
from modules.scraper.utils.scraper_logger import get_scraper_logger
from modules.scraper.utils.text_cleaner import clean_text

# One of these is chosen at random per scraper instance (i.e. per run), not per request,
# so the TLS/HTTP fingerprint stays consistent across all requests in a session.
IMPERSONATE_PROFILES = [
    'chrome116', 'chrome119', 'chrome120', 'chrome123', 'chrome124',
    'chrome131', 'chrome133a', 'chrome136',
    'edge101',
    'safari153', 'safari155', 'safari170', 'safari180', 'safari184',
    'firefox133', 'firefox135',
]

LISTING_URL = 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search'
DETAIL_URL_TEMPLATE = 'https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}'
SEARCH_PAGE_REFERER = 'https://www.linkedin.com/jobs/search'
PAGE_SIZE = 10
REQUEST_TIMEOUT_SECONDS = 15
MAX_JOBS_PER_RUN_ENV_KEY = 'SCRAPER_MAX_JOBS_PER_RUN'
PROXY_HOST_ENV_KEY = 'SCRAPER_PROXY_HOST'
PROXY_PORT_ENV_KEY = 'SCRAPER_PROXY_PORT'
PROXY_USERNAME_ENV_KEY = 'SCRAPER_PROXY_USERNAME'
PROXY_PASSWORD_ENV_KEY = 'SCRAPER_PROXY_PASSWORD'

# DataImpulse session-id parameter (https://docs.dataimpulse.com/proxies/parameters/session-id):
# appending `__sessid.<id>` to the username pins the proxy to one IP until we mint a new session id.
# We rotate that id ourselves every MIN..MAX_PROXY_ROTATION_REQUESTS requests to get a fresh IP.
MIN_PROXY_ROTATION_REQUESTS = 50
MAX_PROXY_ROTATION_REQUESTS = 150
IP_CHECK_URL = 'https://api.ipify.org?format=json'

COMMON_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
}

DEFAULT_SEARCH_FILTERS = {
    'keywords': 'software',
    'location': 'India',
    'f_TPR': 'r86400',
    'f_E': '2,3,4',
    'f_JT': 'F',
}


class LinkedInScraper(BaseScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.LINKEDIN

    def __init__(self):
        self._logger = get_scraper_logger(self.name)
        impersonate_profile = random.choice(IMPERSONATE_PROFILES)
        self._session = requests.Session(impersonate=impersonate_profile)
        self._session.headers.update(COMMON_HEADERS)
        self._logger.info('using impersonate profile: %s', impersonate_profile)

        self._proxy_host = get_env(PROXY_HOST_ENV_KEY)
        self._proxy_port = get_env(PROXY_PORT_ENV_KEY)
        self._proxy_username = get_env(PROXY_USERNAME_ENV_KEY)
        self._proxy_password = get_env(PROXY_PASSWORD_ENV_KEY)
        self._requests_since_rotation = 0
        self._requests_until_rotation = 0
        self._rotate_proxy_session()

        self._max_jobs_per_run = get_env_int(MAX_JOBS_PER_RUN_ENV_KEY)
        self._total_count = 0
        self._total_unique_count = 0
        self._errors: list[dict] = []

    def _build_proxy_url(self, session_id: str) -> str:
        username = f'{self._proxy_username}__sessid.{session_id}'
        return f'http://{username}:{self._proxy_password}@{self._proxy_host}:{self._proxy_port}'

    def _rotate_proxy_session(self) -> None:
        session_id = secrets.token_hex(8)
        proxy_url = self._build_proxy_url(session_id)
        self._session.proxies = {'http': proxy_url, 'https': proxy_url}
        self._requests_since_rotation = 0
        self._requests_until_rotation = random.randint(
            MIN_PROXY_ROTATION_REQUESTS, MAX_PROXY_ROTATION_REQUESTS
        )
        self._logger.info(
            'rotated proxy session id=%s, next rotation after %s requests',
            session_id,
            self._requests_until_rotation,
        )
        self._log_current_proxy_ip()

    def _log_current_proxy_ip(self) -> None:
        try:
            response = self._session.get(IP_CHECK_URL, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            self._logger.info('current proxy egress ip (as seen by LinkedIn): %s', response.json()['ip'])
        except Exception as exc:  # noqa: BLE001 - IP check failure must not abort the run
            self._logger.warning('failed to check proxy egress ip: %s', exc)

    def _request(self, url: str, **kwargs) -> requests.Response:
        if self._requests_since_rotation >= self._requests_until_rotation:
            self._rotate_proxy_session()

        self._requests_since_rotation += 1
        return self._session.get(url, **kwargs)

    def run(self) -> ScraperRunResult:
        self._total_count = 0
        self._total_unique_count = 0
        self._errors = []
        start = 0

        while self._total_count < self._max_jobs_per_run:
            self._logger.info('fetching listing page start=%s', start)
            html = self._fetch_listing_page(start)
            page_listings = self._parse_listing_html(html)

            if not page_listings:
                break

            for listing in page_listings:
                if self._total_count >= self._max_jobs_per_run:
                    break

                self._total_count += 1
                self._process_listing(listing)

            start += PAGE_SIZE
            wait_between_requests()

        self._logger.info(
            'run complete, checked=%s inserted=%s errors=%s',
            self._total_count,
            self._total_unique_count,
            len(self._errors),
        )

        return ScraperRunResult(
            metadata={
                'total_count': self._total_count,
                'total_unique_count': self._total_unique_count,
                'error_count': len(self._errors),
            },
            errors=self._errors,
        )

    def _process_listing(self, listing: dict) -> None:
        url = listing['url']
        job_id = listing['job_id']

        if job_unique_key_service.is_duplicate(url, None):
            self._logger.info('duplicate skipped: %s', url)
            return

        missing_fields = [
            field
            for field in ('url', 'job_id', 'title', 'company_name', 'location')
            if not listing.get(field)
        ]
        if missing_fields:
            message = f'missing required fields: {", ".join(missing_fields)}'
            self._logger.warning('job processing failed for %s: %s', url, message)
            self._errors.append({'url': url, 'message': message})
            return

        try:
            self._logger.info('fetching details for %s', url)
            description = self._fetch_job_details(job_id, referer=url)

            job_service.create_scraped_job(
                title=listing['title'],
                company_name=listing['company_name'],
                location=listing['location'],
                description=description,
                url=url,
            )
        except Exception as exc:  # noqa: BLE001 - one job's failure must not abort the run
            self._logger.warning('job processing failed for %s: %s', url, exc)
            self._errors.append({'url': url, 'message': str(exc)})
            return

        self._total_unique_count += 1
        self._logger.info('job inserted: %s', url)

    def _fetch_listing_page(self, start: int) -> str:
        params = {**DEFAULT_SEARCH_FILTERS, 'start': start}
        response = self._request(
            LISTING_URL,
            params=params,
            headers={'Referer': SEARCH_PAGE_REFERER},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.text

    def _parse_listing_html(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, 'html.parser')
        listings = []

        for card in soup.find_all('li'):
            link = card.find('a', class_='base-card__full-link')
            if link is None or not link.get('href'):
                continue

            raw_url = link['href'].strip()
            job_id = extract_linkedin_job_id(raw_url)
            if job_id is None:
                self._logger.warning('could not extract job id from url: %s', raw_url)
                continue

            title_el = card.find('h3', class_='base-search-card__title')
            company_el = card.find('h4', class_='base-search-card__subtitle')
            location_el = card.find('span', class_='job-search-card__location')

            listings.append(
                {
                    'url': clean_job_url(raw_url),
                    'job_id': job_id,
                    'title': clean_text(title_el.get_text(strip=True) if title_el else None),
                    'company_name': clean_text(company_el.get_text(strip=True) if company_el else None),
                    'location': clean_text(location_el.get_text(strip=True) if location_el else None),
                }
            )

        return listings

    def _fetch_job_details(self, job_id: str, referer: str) -> str | None:
        wait_between_requests()

        detail_url = DETAIL_URL_TEMPLATE.format(job_id=job_id)
        response = self._request(
            detail_url,
            headers={'Referer': referer},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return self._parse_detail_html(response.text)

    def _parse_detail_html(self, html: str) -> str | None:
        soup = BeautifulSoup(html, 'html.parser')
        description_el = soup.find('div', class_='show-more-less-html__markup')
        if description_el is None:
            return None
        return clean_text(description_el.get_text(separator='\n', strip=True))
