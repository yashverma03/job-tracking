from bs4 import BeautifulSoup

from modules.jobs.utils.url_cleaner import clean_job_url
from modules.scraper.base.api_scraper import ApiScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper
from modules.scraper.types import ScraperJobData
from modules.scraper.utils.rate_limiter import wait_between_requests
from modules.scraper.utils.text_cleaner import clean_text

SEARCH_URL = 'https://jobs.natwestgroup.com/search/jobs.json'
DETAIL_URL_TEMPLATE = 'https://jobs.natwestgroup.com/jobs/{job_id}'
COMPANY_NAME = 'NatWest Group'
PAGE_SIZE = 25

DEFAULT_SEARCH_FILTERS = {
    'search_type': 'talemetry',
    'location': 'India',
}


@register_scraper
class NatwestScraper(ApiScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.NATWEST

    @property
    def page_size(self) -> int:
        return PAGE_SIZE

    @property
    def list_url(self) -> str:
        return SEARCH_URL

    @property
    def detail_url(self) -> str:
        return DETAIL_URL_TEMPLATE

    def build_list_params(self, start: int) -> dict:
        return {**DEFAULT_SEARCH_FILTERS, 'page': start // self.page_size + 1}

    def parse_list_items(self, response_json: dict) -> list[dict]:
        return response_json.get('entries', [])

    def map_item_to_listing(self, item: dict) -> ScraperJobData | None:
        job_id = item.get('id')
        if not job_id:
            self._record_error(None, f'missing job id: {item}')
            return None

        location = item.get('location') or {}
        location_text = ', '.join(part for part in (location.get('locality'), location.get('country')) if part)

        return ScraperJobData(
            url=clean_job_url(DETAIL_URL_TEMPLATE.format(job_id=job_id)),
            title=clean_text(item.get('title')),
            company_name=COMPANY_NAME,
            location=clean_text(location_text) if location_text else None,
            extra={'job_id': job_id},
        )

    def build_detail_params(self, listing: ScraperJobData) -> dict:
        return {}

    def _fetch_detail_fields(self, listing: ScraperJobData) -> dict:
        wait_between_requests()
        response = self._request(self.detail_url.format(job_id=listing.extra['job_id']))
        response.raise_for_status()
        return self.parse_detail_fields(response.text)

    def parse_detail_fields(self, html: str) -> dict:
        soup = BeautifulSoup(html, 'html.parser')

        description_el = soup.find('div', id='job-description')
        description = clean_text(description_el.get_text(separator='\n', strip=True)) if description_el else None

        ref_el = soup.find('p', id='job-ref')
        official_id = clean_text(ref_el.get_text(strip=True).lstrip('#')) if ref_el else None

        return {'description': description, 'official_id': official_id}
