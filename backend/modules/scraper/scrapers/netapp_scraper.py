import json

from bs4 import BeautifulSoup

from modules.jobs.utils.url_cleaner import clean_job_url
from modules.scraper.base.api_scraper import ApiScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper
from modules.scraper.types import ListingPage, ScraperJobData
from modules.scraper.utils.text_cleaner import clean_text

LIST_URL = 'https://careers.netapp.com/search-jobs/results'
JOB_BASE_URL = 'https://careers.netapp.com'
COMPANY_NAME = 'NetApp'
RECORDS_PER_PAGE = 10000

# The list endpoint returns everything matching these facets in a single response
# (no real pagination), so only the facet filters relevant to this search need be
# sent - the rest of the site's default query string (module names, radius, custom
# facet params, etc.) is decorative and safely dropped.
DEFAULT_SEARCH_PARAMS = {
    'ActiveFacetID': '8604160',
    'CurrentPage': 1,
    'RecordsPerPage': RECORDS_PER_PAGE,
    'Distance': 50,
    'RadiusUnitType': 0,
    'Keywords': '',
    'Location': 'India',
    'ShowRadius': 'False',
    'IsPagination': 'False',
    'FacetFilters[0].ID': '8604160',
    'FacetFilters[0].FacetType': 1,
    'FacetFilters[0].Display': 'Engineering',
    'FacetFilters[0].IsApplied': 'true',
    'FacetFilters[1].ID': '8604176',
    'FacetFilters[1].FacetType': 1,
    'FacetFilters[1].Display': 'Information Technology',
    'FacetFilters[1].IsApplied': 'true',
    'FacetFilters[2].ID': '8604192',
    'FacetFilters[2].FacetType': 1,
    'FacetFilters[2].Display': 'Software Engineering',
    'FacetFilters[2].IsApplied': 'true',
    'FacetFilters[3].ID': '1269750',
    'FacetFilters[3].FacetType': 2,
    'FacetFilters[3].Display': 'India',
    'FacetFilters[3].IsApplied': 'true',
    'SearchResultsModuleName': 'Search Results',
    'SearchFiltersModuleName': 'Search Filters',
    'SortCriteria': 2,
    'SortDirection': 0,
    'SearchType': 6,
    'OrganizationIds': '27600',
    'ResultsType': 0,
}

@register_scraper
class NetappScraper(ApiScraper):
    @property
    def name(self) -> ScraperName:
        return ScraperName.NETAPP

    @property
    def page_size(self) -> int:
        return RECORDS_PER_PAGE

    @property
    def list_url(self) -> str:
        return LIST_URL

    @property
    def detail_url(self) -> str:
        return JOB_BASE_URL

    def build_list_params(self, start: int) -> dict:
        return dict(DEFAULT_SEARCH_PARAMS)

    def parse_list_items(self, response_json: dict) -> list[dict]:
        soup = BeautifulSoup(response_json.get('results') or '', 'html.parser')
        items = []
        for link in soup.select('#search-results-list a[data-job-id]'):
            title_el = link.find('h3')
            location_el = link.find('span', class_='job-location')
            items.append(
                {
                    'job_id': link.get('data-job-id'),
                    'href': link.get('href'),
                    'title': title_el.get_text(strip=True) if title_el else None,
                    'location': location_el.get_text(strip=True) if location_el else None,
                }
            )
        return items

    def map_item_to_listing(self, item: dict) -> ScraperJobData | None:
        job_id = item.get('job_id')
        href = item.get('href')
        if not job_id or not href:
            self._record_error(None, f'missing job id or href: {item}')
            return None

        return ScraperJobData(
            url=clean_job_url(f'{JOB_BASE_URL}{href}'),
            official_id=str(job_id),
            title=clean_text(item.get('title')),
            company_name=COMPANY_NAME,
            location=clean_text(item.get('location')),
        )

    def build_detail_params(self, listing: ScraperJobData) -> dict:
        return {}

    def _fetch_listing_page(self, start: int, time_range_hours: int) -> ListingPage:
        # Everything matching the search facets comes back in one response - no
        # offset/page param actually changes the result set, so always stop after it.
        response = self._request(self.list_url, params=self.build_list_params(start))
        response.raise_for_status()
        items = self.parse_list_items(response.json())

        listings = []
        for item in items:
            listing = self.map_item_to_listing(item)
            if listing is not None:
                listings.append(listing)

        return ListingPage(listings=listings, stop=True)

    def _fetch_detail_fields(self, listing: ScraperJobData) -> dict:
        response = self._request(listing.url)
        response.raise_for_status()
        return self.parse_detail_fields(response.text)

    def parse_detail_fields(self, html: str) -> dict:
        soup = BeautifulSoup(html, 'html.parser')
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string or '')
            except (TypeError, ValueError):
                continue
            if data.get('@type') == 'JobPosting':
                return {'description': clean_text(data.get('description'))}

        return {'description': None}
