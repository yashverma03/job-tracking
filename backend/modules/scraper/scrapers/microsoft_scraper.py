import time

from common.utils.http import get_with_retry
from modules.jobs.utils.url_cleaner import clean_job_url
from modules.scraper.base.base_scraper import BaseScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.types import ListingPage, ScraperJobData
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

    @property
    def page_size(self) -> int:
        return PAGE_SIZE

    def __init__(self):
        super().__init__()

        self._session = new_session()
        self._session.headers['User-Agent'] = get_random_user_agent()

    def _request(self, url: str, **kwargs):
        return get_with_retry(lambda: self._session, url, **kwargs)

    def _fetch_listing_page(self, start: int, time_range_hours: int) -> ListingPage:
        cutoff_ts = int(time.time()) - time_range_hours * SECONDS_PER_HOUR

        params = {**DEFAULT_SEARCH_FILTERS, 'start': start}
        response = self._request(SEARCH_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        positions = response.json().get('data', {}).get('positions', [])

        if not positions:
            self._logger.info('stopping pagination, got an empty page')
            return ListingPage(stop=True)

        listings = []
        for position in positions:
            posted_ts = position.get('postedTs') or position.get('creationTs')
            if posted_ts is not None and posted_ts < cutoff_ts:
                continue

            listing = self._to_listing(position)
            if listing is not None:
                listings.append(listing)

        return ListingPage(listings=listings)

    def _to_listing(self, position: dict) -> ScraperJobData | None:
        position_id = position.get('id')
        display_job_id = position.get('displayJobId')
        if position_id is None or not display_job_id:
            message = 'missing position id or displayJobId'
            self._logger.warning('%s: %s', message, position)
            self._errors.append({'url': None, 'message': message})
            return None

        locations = position.get('locations') or position.get('standardizedLocations') or []

        return ScraperJobData(
            url=clean_job_url(JOB_URL_TEMPLATE.format(position_id=position_id)),
            official_id=str(display_job_id),
            title=clean_text(position.get('name')),
            company_name=COMPANY_NAME,
            location=clean_text('; '.join(locations)) if locations else None,
            extra={'position_id': position_id},
        )

    def _fetch_detail_fields(self, listing: ScraperJobData) -> dict:
        return {'description': self._fetch_job_details(listing.extra['position_id'])}

    def _fetch_job_details(self, position_id: int) -> str | None:
        wait_between_requests()

        params = {'position_id': position_id, 'domain': 'microsoft.com', 'hl': 'en'}
        response = self._request(DETAIL_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        description = response.json().get('data', {}).get('jobDescription')
        return clean_text(description)
