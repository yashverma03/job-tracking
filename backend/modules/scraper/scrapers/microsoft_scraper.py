from modules.jobs.utils.url_cleaner import clean_job_url
from modules.scraper.base.api_scraper import ApiScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper
from modules.scraper.types import ScraperJobData
from modules.scraper.utils.text_cleaner import clean_text
from modules.scraper.utils.time_range import is_within_time_range

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


@register_scraper
class MicrosoftScraper(ApiScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.MICROSOFT

    @property
    def page_size(self) -> int:
        return PAGE_SIZE

    @property
    def list_url(self) -> str:
        return SEARCH_URL

    @property
    def detail_url(self) -> str:
        return DETAIL_URL

    def build_list_params(self, start: int) -> dict:
        return {**DEFAULT_SEARCH_FILTERS, 'start': start}

    def parse_list_items(self, response_json: dict) -> list[dict]:
        return response_json.get('data', {}).get('positions', [])

    def is_item_in_time_range(self, item: dict, time_range_hours: int) -> bool:
        posted_ts = item.get('postedTs') or item.get('creationTs')
        return is_within_time_range(posted_ts, time_range_hours)

    def map_item_to_listing(self, item: dict) -> ScraperJobData | None:
        position_id = item.get('id')
        display_job_id = item.get('displayJobId')
        if position_id is None or not display_job_id:
            self._record_error(None, f'missing position id or displayJobId: {item}')
            return None

        locations = item.get('locations') or item.get('standardizedLocations') or []

        return ScraperJobData(
            url=clean_job_url(JOB_URL_TEMPLATE.format(position_id=position_id)),
            official_id=str(display_job_id),
            title=clean_text(item.get('name')),
            company_name=COMPANY_NAME,
            location=clean_text('; '.join(locations)) if locations else None,
            extra={'position_id': position_id},
        )

    def build_detail_params(self, listing: ScraperJobData) -> dict:
        return {'position_id': listing.extra['position_id'], 'domain': 'microsoft.com', 'hl': 'en'}

    def parse_detail_fields(self, response_json: dict) -> dict:
        description = response_json.get('data', {}).get('jobDescription')
        return {'description': clean_text(description)}
