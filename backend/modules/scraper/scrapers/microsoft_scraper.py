import time
from concurrent.futures import Future, ThreadPoolExecutor, wait as wait_futures

from curl_cffi.requests.exceptions import HTTPError

from common.utils.http import get_with_retry
from modules.jobs.utils.url_cleaner import clean_job_url
from modules.scraper.base.base_scraper import BaseScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.types import ScraperRunResult
from modules.scraper.constants import REQUEST_TIMEOUT_SECONDS, SECONDS_PER_HOUR
from modules.scraper.utils.http_session import new_session
from modules.scraper.utils.rate_limiter import wait_between_requests
from modules.scraper.utils.text_cleaner import clean_text
from modules.scraper.utils.user_agent_rotator import get_random_user_agent

SEARCH_URL = 'https://apply.careers.microsoft.com/api/pcsx/search'
DETAIL_URL = 'https://apply.careers.microsoft.com/api/pcsx/position_details'
JOB_URL_TEMPLATE = 'https://apply.careers.microsoft.com/careers/job/{position_id}'
COMPANY_NAME = 'Microsoft'
PAGE_SIZE = 10

DEFAULT_SEARCH_FILTERS = {
    'domain': 'microsoft.com',
    'query': '',
    'location': 'India',
    'sort_by': 'timestamp',
    'filter_include_remote': '1',
    'filter_career_discipline': 'Software Engineering',
    'filter_employment_type': 'full-time',
    'filter_roletype': 'individual contributor',
    'filter_profession': 'software engineering',
}


class MicrosoftScraper(BaseScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.MICROSOFT

    def __init__(self):
        super().__init__()

        # Single plain session for the whole run (no proxy) with one randomized
        # fingerprint (TLS impersonate profile + user agent) set up once.
        self._session = new_session()
        self._session.headers['User-Agent'] = get_random_user_agent()

        self._total_count = 0

    def _request(self, url: str, **kwargs):
        return get_with_retry(lambda: self._session, url, **kwargs)

    def run(self, max_jobs_per_run: int, start_offset: int, time_range_hours: int) -> ScraperRunResult:
        self._total_count = 0
        self._reset_run_state()
        cutoff_ts = int(time.time()) - time_range_hours * SECONDS_PER_HOUR
        start = start_offset
        pending: list[Future] = []

        with ThreadPoolExecutor(max_workers=self.detail_worker_count, thread_name_prefix='microsoft-detail') as executor:
            while self._total_count < max_jobs_per_run:
                self._logger.info('fetching listing page start=%s', start)
                try:
                    positions = self._fetch_listing_page(start)
                except HTTPError as exc:
                    status_code = exc.response.status_code if exc.response is not None else None
                    if status_code is not None and 400 <= status_code < 500:
                        self._logger.warning('stopping pagination, listing page failed with %s', exc)
                        break
                    raise

                if not positions:
                    self._logger.info('stopping pagination, got an empty page')
                    break

                for position in positions:
                    if self._total_count >= max_jobs_per_run:
                        break

                    # Don't assume the API's sort order actually holds - just filter
                    # out anything older than the cutoff instead of stopping early.
                    posted_ts = position.get('postedTs') or position.get('creationTs')
                    if posted_ts is not None and posted_ts < cutoff_ts:
                        continue

                    listing = self._to_listing(position)
                    if listing is None:
                        continue

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
        return self._fetch_job_details(listing['position_id'])

    def _fetch_listing_page(self, start: int) -> list[dict]:
        params = {**DEFAULT_SEARCH_FILTERS, 'start': start}
        response = self._request(SEARCH_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json().get('data', {}).get('positions', [])

    def _to_listing(self, position: dict) -> dict | None:
        position_id = position.get('id')
        display_job_id = position.get('displayJobId')
        if position_id is None or not display_job_id:
            message = 'missing position id or displayJobId'
            self._logger.warning('%s: %s', message, position)
            self._errors.append({'url': None, 'message': message})
            return None

        locations = position.get('locations') or position.get('standardizedLocations') or []

        return {
            'url': clean_job_url(JOB_URL_TEMPLATE.format(position_id=position_id)),
            'position_id': position_id,
            'official_id': str(display_job_id),
            'title': clean_text(position.get('name')),
            'company_name': COMPANY_NAME,
            'location': clean_text('; '.join(locations)) if locations else None,
        }

    def _fetch_job_details(self, position_id: int) -> str | None:
        wait_between_requests()

        params = {'position_id': position_id, 'domain': 'microsoft.com', 'hl': 'en'}
        response = self._request(DETAIL_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        description = response.json().get('data', {}).get('jobDescription')
        return clean_text(description)
