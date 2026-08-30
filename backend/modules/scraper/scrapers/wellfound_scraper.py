import re
import time

from common.utils.env import get_env
from common.utils.http import post_with_retry
from modules.jobs.utils.url_cleaner import clean_job_url
from modules.scraper.base.api_scraper import ApiScraper
from modules.scraper.constants import REQUEST_TIMEOUT_SECONDS, SECONDS_PER_HOUR
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper
from modules.scraper.types import ListingPage, ScraperJobData
from modules.scraper.utils.text_cleaner import clean_text

GRAPHQL_URL = 'https://wellfound.com/graphql'
LOGIN_URL = 'https://wellfound.com/login'
JOB_URL_TEMPLATE = 'https://wellfound.com/jobs/{job_id}-{slug}'
PAGE_SIZE = 1  # `start` is used directly as the GraphQL `page` number, advanced by 1 each call.

EMAIL_ENV_KEY = 'SCRAPER_WELLFOUND_EMAIL'
PASSWORD_ENV_KEY = 'SCRAPER_WELLFOUND_PASSWORD'

CSRF_TOKEN_PATTERN = re.compile(r'name="csrf-token" content="([^"]+)"')

SEARCH_OPERATION_ID = 'tfe/5f366cd305b4f13cf6098df75f7ff2bb92fa42b9a74cb3a3aec7bdc69c6b051e'
DETAIL_OPERATION_ID = 'tfe/e32faab6776e2e8617eefb0dada42582512247d281de5a7bf30fb8f7e695e787'

DEFAULT_FILTER_CONFIGURATION = {
    'roleTagIds': ['14726', '151647', '151718', '751460'],
    'companySizes': [
        'SIZE_11_50',
        'SIZE_51_200',
        'SIZE_201_500',
        'SIZE_501_1000',
        'SIZE_1001_5000',
        'SIZE_5000_PLUS',
    ],
    'equity': {'min': None, 'max': None},
    'includeJobsWithoutExperience': True,
    'jobTypes': ['full_time'],
    'excludedKeywords': ['Staff software', 'Lead software', 'SDET'],
    'includeJobsWithoutSalary': True,
    'remotePreference': 'REMOTE_OPEN',
    'salary': {'min': 13, 'max': None},
    'yearsExperience': {'min': 2, 'max': 3},
}


@register_scraper
class WellfoundScraper(ApiScraper):
    """Wellfound's list/detail API is plain (Apollo persisted) GraphQL behind an
    authenticated session - a bespoke shape for this one site, not a shared vendor ATS,
    so this extends `ApiScraper` directly rather than a new platform base class.

    Both endpoints are POST-only, so `_fetch_listing_page`/`_fetch_detail_fields` are
    overridden (same pattern as `WorkdayScraper`) instead of relying on `ApiScraper`'s
    default GET-based fetch."""

    @property
    def name(self) -> ScraperName:
        return ScraperName.WELLFOUND

    @property
    def page_size(self) -> int:
        return PAGE_SIZE

    @property
    def list_url(self) -> str:
        return GRAPHQL_URL

    @property
    def detail_url(self) -> str:
        return GRAPHQL_URL

    def __init__(self):
        super().__init__()
        self._session.headers.update(
            {
                'apollographql-client-name': 'talent-web',
                'x-requested-with': 'XMLHttpRequest',
                'Origin': 'https://wellfound.com',
            }
        )
        self._login()

    def _login(self) -> None:
        email = get_env(EMAIL_ENV_KEY)
        password = get_env(PASSWORD_ENV_KEY)

        login_page = self._request(LOGIN_URL)
        login_page.raise_for_status()
        match = CSRF_TOKEN_PATTERN.search(login_page.text)
        if match is None:
            raise RuntimeError('could not find csrf token on Wellfound login page')

        response = post_with_retry(
            lambda: self._session,
            LOGIN_URL,
            data={
                'utf8': '✓',
                'authenticity_token': match.group(1),
                'login_only': 'true',
                'username': email,
                'password': password,
                'commit': 'Log in',
            },
            headers={'Referer': LOGIN_URL},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()

        if not self._session.cookies.get('_wellfound'):
            raise RuntimeError('Wellfound login failed: no session cookie set after login attempt')

        self._logger.info('logged into Wellfound as %s', email)

    def build_list_params(self, start: int) -> dict:
        return {
            'operationName': 'JobSearchResultsX',
            'variables': {'filterConfigurationInput': {**DEFAULT_FILTER_CONFIGURATION, 'page': start}},
            'extensions': {'operationId': SEARCH_OPERATION_ID},
        }

    def _startup_nodes(self, edges: list[dict]) -> list[dict]:
        """Flatten each search-result edge into a list of startup-shaped nodes. Most
        edges' `node` already is one (a plain `StartupSearchResult` or a `PromotedResult`
        wrapping one in `promotedStartup`), but a `FeaturedStartups` node instead wraps
        several such startups in `featuredStartups` - unwrap those too, or every job
        listing nested inside them is silently dropped."""
        startups = []
        for edge in edges:
            node = edge.get('node') or {}
            if node.get('__typename') == 'FeaturedStartups':
                startups.extend(node.get('featuredStartups') or [])
            else:
                startups.append(node)
        return startups

    def parse_list_items(self, response_json: dict) -> list[dict]:
        edges = response_json.get('data', {}).get('talent', {}).get('jobSearchResults', {}).get('startups', {}).get(
            'edges', []
        )

        items = []
        for node in self._startup_nodes(edges):
            startup = node.get('promotedStartup') or node
            startup_name = startup.get('name')
            for job_listing in startup.get('highlightedJobListings') or []:
                items.append({**job_listing, '_startup_name': startup_name})
        return items

    def map_item_to_listing(self, item: dict) -> ScraperJobData | None:
        job_id = item.get('id')
        slug = item.get('slug')
        if not job_id or not slug:
            self._record_error(None, f'missing id or slug: {item}')
            return None

        location_names = item.get('locationNames') or []
        location = '; '.join(location_names) if location_names else ('Remote' if item.get('remote') else None)

        return ScraperJobData(
            url=clean_job_url(JOB_URL_TEMPLATE.format(job_id=job_id, slug=slug)),
            official_id=str(job_id),
            title=clean_text(item.get('title')),
            company_name=clean_text(item.get('_startup_name')),
            location=clean_text(location),
            extra={'job_id': job_id, 'slug': slug},
        )

    def build_detail_params(self, listing: ScraperJobData) -> dict:
        return {
            'operationName': 'JobListingModalQuery',
            'variables': {'id': listing.extra['job_id'], 'slug': listing.extra['slug']},
            'extensions': {'operationId': DETAIL_OPERATION_ID},
        }

    def parse_detail_fields(self, response_json: dict) -> dict:
        job_listing = response_json.get('data', {}).get('jobListing') or {}
        description = clean_text(job_listing.get('descriptionHtml') or job_listing.get('description'))
        compensation = job_listing.get('compensation')

        if compensation:
            description = f'Salary: {compensation}\n\n{description}' if description else f'Salary: {compensation}'

        return {'description': description}

    def _fetch_listing_page(self, start: int, time_range_hours: int) -> ListingPage:
        response = post_with_retry(
            lambda: self._session,
            self.list_url,
            json=self.build_list_params(start),
            headers={'Referer': 'https://wellfound.com/jobs'},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        response_json = response.json()
        items = self.parse_list_items(response_json)

        if not items:
            self._logger.info('stopping pagination, got an empty page')
            return ListingPage(stop=True)

        cutoff = time.time() - time_range_hours * SECONDS_PER_HOUR
        listings = []
        for item in items:
            live_start_at = item.get('liveStartAt')
            if isinstance(live_start_at, (int, float)) and live_start_at < cutoff:
                continue
            listing = self.map_item_to_listing(item)
            if listing is not None:
                listings.append(listing)

        has_next_page = response_json.get('data', {}).get('talent', {}).get('jobSearchResults', {}).get(
            'hasNextPage', False
        )
        return ListingPage(listings=listings, stop=not has_next_page)

    def _fetch_detail_fields(self, listing: ScraperJobData) -> dict:
        response = post_with_retry(
            lambda: self._session,
            self.detail_url,
            json=self.build_detail_params(listing),
            headers={'Referer': listing.url},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return self.parse_detail_fields(response.json())
