import secrets
import threading
from concurrent.futures import Future, ThreadPoolExecutor, wait as wait_futures

from bs4 import BeautifulSoup
from curl_cffi import requests
from curl_cffi.requests.exceptions import HTTPError

from common.utils.env import get_env
from common.utils.http import get_with_retry
from modules.jobs.utils.url_cleaner import clean_job_url, extract_linkedin_job_id
from modules.scraper.base.base_scraper import BaseScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.types import ScraperRunResult
from modules.scraper.constants import REQUEST_TIMEOUT_SECONDS, SECONDS_PER_HOUR
from modules.scraper.utils.http_session import new_session
from modules.scraper.utils.rate_limiter import wait_between_requests
from modules.scraper.utils.text_cleaner import clean_text

LISTING_URL = 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search'
DETAIL_URL_TEMPLATE = 'https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}'
SEARCH_PAGE_REFERER = 'https://www.linkedin.com/jobs/search'
PAGE_SIZE = 10
MAX_CONSECUTIVE_EMPTY_PAGES = 5
PROXY_HOST_ENV_KEY = 'SCRAPER_PROXY_HOST'
PROXY_PORT_ENV_KEY = 'SCRAPER_PROXY_PORT'
PROXY_USERNAME_ENV_KEY = 'SCRAPER_PROXY_USERNAME'
PROXY_PASSWORD_ENV_KEY = 'SCRAPER_PROXY_PASSWORD'

DEFAULT_SEARCH_FILTERS = {
    'keywords': 'software',
    'location': 'India',
    'f_E': '2,3,4',
    'f_JT': 'F',
}


def _new_session(scraper: 'LinkedInScraper') -> requests.Session:
    """Build a fresh session with a new proxy exit IP (a fresh random impersonate
    profile/fingerprint is handled by new_session itself)."""
    proxy_url = scraper._build_proxy_url(secrets.token_hex(8))
    return new_session(proxy_url)


class _ProxyLane:
    """A session used by one worker thread at a time. On retry the current session is discarded
    and a brand new one is used instead, since a failure is usually tied to the specific IP/fingerprint
    combo."""

    def __init__(self, scraper: 'LinkedInScraper', label: str):
        self._scraper = scraper
        self._label = label
        self.session = _new_session(scraper)

    def request(self, url: str, **kwargs) -> requests.Response:
        def on_retry():
            self.session = _new_session(self._scraper)

        return get_with_retry(lambda: self.session, url, on_retry=on_retry, **kwargs)


class LinkedInScraper(BaseScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.LINKEDIN

    def __init__(self):
        super().__init__()

        self._proxy_host = get_env(PROXY_HOST_ENV_KEY)
        self._proxy_port = get_env(PROXY_PORT_ENV_KEY)
        self._proxy_username = get_env(PROXY_USERNAME_ENV_KEY)
        self._proxy_password = get_env(PROXY_PASSWORD_ENV_KEY)

        # Dedicated lane for sequential listing-page pagination requests.
        self._listing_lane = _ProxyLane(self, label='listing')

        # Lazily-created, one-per-thread lanes for concurrent job detail fetches.
        self._thread_local = threading.local()
        self._lane_counter = 0
        self._lane_counter_lock = threading.Lock()

        self._total_count = 0

    def _build_proxy_url(self, session_id: str) -> str:
        username = f'{self._proxy_username}__sessid.{session_id}'
        return f'http://{username}:{self._proxy_password}@{self._proxy_host}:{self._proxy_port}'

    def _get_detail_lane(self) -> _ProxyLane:
        lane = getattr(self._thread_local, 'lane', None)
        if lane is None:
            with self._lane_counter_lock:
                self._lane_counter += 1
                label = f'detail-{self._lane_counter}'
            lane = _ProxyLane(self, label=label)
            self._thread_local.lane = lane
        return lane

    def _request(self, url: str, **kwargs) -> requests.Response:
        return self._listing_lane.request(url, **kwargs)

    def run(self, max_jobs_per_run: int, start_offset: int, time_range_hours: int) -> ScraperRunResult:
        self._total_count = 0
        self._reset_run_state()
        self._time_range_seconds = time_range_hours * SECONDS_PER_HOUR
        start = start_offset
        consecutive_empty_pages = 0
        pending: list[Future] = []

        with ThreadPoolExecutor(max_workers=self.detail_worker_count, thread_name_prefix='linkedin-detail') as executor:
            while self._total_count < max_jobs_per_run:
                self._logger.info('fetching listing page start=%s', start)
                try:
                    html = self._fetch_listing_page(start)
                except HTTPError as exc:
                    status_code = exc.response.status_code if exc.response is not None else None
                    if status_code is not None and 400 <= status_code < 500:
                        self._logger.warning('stopping pagination, listing page failed with %s', exc)
                        break
                    raise
                page_listings = self._parse_listing_html(html)

                if not page_listings:
                    consecutive_empty_pages += 1
                    if consecutive_empty_pages >= MAX_CONSECUTIVE_EMPTY_PAGES:
                        self._logger.info('stopping pagination after %s consecutive empty pages', consecutive_empty_pages)
                        break
                    start += PAGE_SIZE
                    wait_between_requests()
                    continue

                consecutive_empty_pages = 0

                for listing in page_listings:
                    if self._total_count >= max_jobs_per_run:
                        break

                    self._total_count += 1
                    pending.append(executor.submit(self.add_job_from_listing, listing))

                start += PAGE_SIZE
                wait_between_requests()

            wait_futures(pending)
            for future in pending:
                future.result()  # surface any unexpected (non-per-job) exception

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

    def _fetch_description(self, listing: dict) -> str | None:
        return self._fetch_job_details(listing['job_id'], referer=listing['url'])

    def _fetch_listing_page(self, start: int) -> str:
        params = {**DEFAULT_SEARCH_FILTERS, 'f_TPR': f'r{self._time_range_seconds}', 'start': start}
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
                message = 'could not extract job id from url'
                self._logger.warning('%s: %s', message, raw_url)
                self._errors.append({'url': raw_url, 'message': message})
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
        response = self._get_detail_lane().request(
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
