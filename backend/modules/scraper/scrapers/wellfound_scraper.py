import atexit
import json
import re
from concurrent.futures import ThreadPoolExecutor

from playwright.sync_api import sync_playwright

from common.utils.env import get_env
from modules.jobs.utils.url_cleaner import clean_job_url
from modules.scraper.base.base_scraper import BaseScraper
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper
from modules.scraper.types import ListingPage, ScraperJobData
from modules.scraper.utils.text_cleaner import clean_text

LOGIN_URL = 'https://wellfound.com/login'
JOBS_URL = 'https://wellfound.com/jobs'
JOB_URL_TEMPLATE = 'https://wellfound.com/jobs/{job_id}-{slug}'
NEXT_DATA_PATTERN = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)

EMAIL_ENV_KEY = 'SCRAPER_WELLFOUND_EMAIL'
PASSWORD_ENV_KEY = 'SCRAPER_WELLFOUND_PASSWORD'

NAVIGATION_TIMEOUT_MS = 45000
SETTLE_WAIT_MS = 3000
SCROLL_PX = 4000
SCROLL_UP_PX = 800
SCROLL_WAIT_MS = 2500
MAX_SCROLL_PAGES = 10
SCROLL_RETRIES_PER_PAGE = 3


def _job_search_page_number(response) -> int | None:
    try:
        request_body = response.request.post_data_json
    except Exception:  # noqa: BLE001
        return None
    if not isinstance(request_body, dict):
        return None
    return request_body.get('variables', {}).get('filterConfigurationInput', {}).get('page')


def _job_search_results(response) -> dict | None:
    if 'graphql' not in response.url:
        return None
    try:
        body = response.json()
    except Exception:  # noqa: BLE001
        return None
    if not isinstance(body, dict):
        return None
    if body.get('data', {}).get('talent', {}).get('jobSearchResults') is None:
        return None
    return body


@register_scraper
class WellfoundScraper(BaseScraper):
    """Drives a real headless browser via Playwright instead of extending
    `ApiScraper`, since Wellfound's GraphQL endpoint rejects plain HTTP requests.

    All Playwright calls run on one dedicated thread (`_browser_executor`), since
    `BaseScraper.run` calls the listing and detail hooks from different threads."""

    @property
    def name(self) -> ScraperName:
        return ScraperName.WELLFOUND

    @property
    def page_size(self) -> int:
        return 1

    @property
    def detail_worker_count(self) -> int:
        return 1

    def __init__(self):
        super().__init__()
        self._captured_responses: list[dict] = []
        self._captured_pages: set[int] = set()
        self._browser_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='wellfound-browser')
        self._run_on_browser_thread(self._start_browser)

    def _run_on_browser_thread(self, fn, *args, **kwargs):
        return self._browser_executor.submit(fn, *args, **kwargs).result()

    def _start_browser(self) -> None:
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)
        self._context = self._browser.new_context()
        self._page = self._context.new_page()
        self._page.on('response', self._on_response)
        atexit.register(self._shutdown_browser)
        self._login()

    def _on_response(self, response) -> None:
        results = _job_search_results(response)
        if results is None:
            return
        self._captured_responses.append(results)
        page_number = _job_search_page_number(response)
        if page_number is not None:
            self._captured_pages.add(page_number)

    def _shutdown_browser(self) -> None:
        try:
            self._browser.close()
            self._playwright.stop()
        except Exception:  # noqa: BLE001
            pass

    def _login(self) -> None:
        email = get_env(EMAIL_ENV_KEY)
        password = get_env(PASSWORD_ENV_KEY)

        self._page.goto(LOGIN_URL, wait_until='load', timeout=NAVIGATION_TIMEOUT_MS)
        self._page.fill('input[name=username]', email)
        self._page.fill('input[name=password]', password)
        with self._page.expect_navigation(timeout=30000):
            self._page.click('input[type=submit]')

        if not any(cookie.get('name') == '_wellfound' for cookie in self._context.cookies()):
            raise RuntimeError('Wellfound login failed: no session cookie set after login attempt')

        self._logger.info('logged into Wellfound as %s', email)

    def _startup_nodes(self, edges: list[dict]) -> list[dict]:
        startups = []
        for edge in edges:
            node = edge.get('node') or {}
            if node.get('__typename') == 'FeaturedStartups':
                startups.extend(node.get('featuredStartups') or [])
            else:
                startups.append(node)
        return startups

    def _parse_list_items(self, response_json: dict) -> list[dict]:
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

    def _map_item_to_listing(self, item: dict) -> ScraperJobData | None:
        job_id = item.get('id')
        slug = item.get('slug')
        if not job_id or not slug:
            self._record_error(None, f'missing id or slug: {item}')
            return None

        location_names = item.get('locationNames') or []
        location = '; '.join(location_names) if location_names else ('Remote' if item.get('remote') else None)

        return ScraperJobData(
            url=clean_job_url(JOB_URL_TEMPLATE.format(job_id=job_id, slug=slug)),
            title=clean_text(item.get('title')),
            company_name=clean_text(item.get('_startup_name')),
            location=clean_text(location),
            extra={'job_id': job_id, 'slug': slug},
        )

    def _fetch_listing_page(self, start: int, time_range_hours: int) -> ListingPage:
        if start > 0:
            return ListingPage(stop=True)
        return self._run_on_browser_thread(self._fetch_all_listings_on_browser_thread)

    def _sort_by_most_recent(self) -> None:
        self._page.get_by_text('Recommended', exact=True).first.click()
        self._page.wait_for_timeout(300)
        self._page.get_by_text('Most recent', exact=True).first.click()

    def _fetch_all_listings_on_browser_thread(self) -> ListingPage:
        self._captured_responses = []
        self._captured_pages = set()

        self._page.goto(JOBS_URL, wait_until='load', timeout=NAVIGATION_TIMEOUT_MS)
        self._sort_by_most_recent()
        self._page.wait_for_timeout(SETTLE_WAIT_MS)

        for page_num in range(MAX_SCROLL_PAGES):
            pages_before = len(self._captured_pages)
            for _ in range(SCROLL_RETRIES_PER_PAGE):
                self._page.mouse.wheel(0, -SCROLL_UP_PX)
                self._page.wait_for_timeout(200)
                self._page.mouse.wheel(0, SCROLL_PX)
                self._page.wait_for_timeout(SCROLL_WAIT_MS)
                if len(self._captured_pages) > pages_before:
                    break
            else:
                self._logger.info(
                    'scroll page %s/%s did not advance to a new page after %s retries, pages seen=%s',
                    page_num + 1,
                    MAX_SCROLL_PAGES,
                    SCROLL_RETRIES_PER_PAGE,
                    sorted(self._captured_pages),
                )

        seen_job_ids = set()
        listings = []
        for response_json in self._captured_responses:
            for item in self._parse_list_items(response_json):
                job_id = item.get('id')
                if job_id is None or job_id in seen_job_ids:
                    continue
                seen_job_ids.add(job_id)

                listing = self._map_item_to_listing(item)
                if listing is not None:
                    listings.append(listing)

        self._logger.info(
            'captured %s page responses, %s unique jobs after dedup/time filter',
            len(self._captured_responses),
            len(listings),
        )
        return ListingPage(listings=listings, stop=True)

    def _fetch_detail_fields(self, listing: ScraperJobData) -> dict:
        return self._run_on_browser_thread(self._fetch_detail_fields_on_browser_thread, listing)

    def _fetch_detail_fields_on_browser_thread(self, listing: ScraperJobData) -> dict:
        self._page.goto(listing.url, wait_until='load', timeout=NAVIGATION_TIMEOUT_MS)
        html = self._page.content()

        match = NEXT_DATA_PATTERN.search(html)
        if match is None:
            raise RuntimeError(f'could not find __NEXT_DATA__ on {listing.url}')

        next_data = json.loads(match.group(1))
        apollo_data = next_data.get('props', {}).get('pageProps', {}).get('apolloState', {}).get('data', {})
        job_listing = apollo_data.get(f'JobListing:{listing.extra["job_id"]}') or {}

        description = clean_text(job_listing.get('descriptionHtml') or job_listing.get('description'))
        compensation = job_listing.get('compensation')
        if compensation:
            description = f'Salary: {compensation}\n\n{description}' if description else f'Salary: {compensation}'

        return {'description': description}
