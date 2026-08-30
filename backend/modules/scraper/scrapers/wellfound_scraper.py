import atexit
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from common.utils.env import get_env
from modules.jobs.utils.url_cleaner import clean_job_url
from modules.scraper.base.base_scraper import BaseScraper
from modules.scraper.constants import SECONDS_PER_HOUR
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import register_scraper
from modules.scraper.types import ListingPage, ScraperJobData
from modules.scraper.utils.rate_limiter import wait_between_requests
from modules.scraper.utils.text_cleaner import clean_text

LOGIN_URL = 'https://wellfound.com/login'
JOBS_URL = 'https://wellfound.com/jobs'
JOB_URL_TEMPLATE = 'https://wellfound.com/jobs/{job_id}-{slug}'
NEXT_DATA_PATTERN = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)

EMAIL_ENV_KEY = 'SCRAPER_WELLFOUND_EMAIL'
PASSWORD_ENV_KEY = 'SCRAPER_WELLFOUND_PASSWORD'

NAVIGATION_TIMEOUT_MS = 45000
RESPONSE_WAIT_TIMEOUT_MS = 15000
SCROLL_PX = 4000
MAX_SCROLL_ATTEMPTS = 10


def _is_job_search_response(response) -> bool:
    if 'graphql' not in response.url:
        return False
    try:
        body = response.request.post_data_json
    except Exception:  # noqa: BLE001 - a request with a non-JSON body just isn't a match
        return False
    return bool(body) and body.get('operationName') == 'JobSearchResultsX'


@register_scraper
class WellfoundScraper(BaseScraper):
    """Wellfound protects its GraphQL endpoint with per-request signature headers
    (`x-apollo-signature`, `x-wf-cfp`) that its own Apollo Client middleware computes -
    confirmed by testing that a hand-built request, even with a fully authenticated
    session's cookies attached, gets hard-blocked with a Cloudflare/Turnstile "Security
    Check" challenge page. No plain HTTP client can produce a valid one, so unlike
    every other scraper here this can't extend `ApiScraper` - it drives a real
    (headless) browser via Playwright instead, letting Wellfound's own page code build
    and send every request.

    Listing: the account's search filters are saved server-side, so simply loading
    `/jobs` re-fires `JobSearchResultsX` with them already applied (verified against
    this account); further pages come from the same infinite-scroll requests a real
    user's scrolling would trigger.

    Detail: navigating straight to a job's URL renders it server-side with the full
    listing (including `descriptionHtml`/`compensation`) embedded in a Next.js
    `__NEXT_DATA__` Apollo-cache blob - no click-through or second GraphQL call needed.

    All Playwright calls are funnelled through one dedicated thread
    (`_browser_executor`, max_workers=1): the sync Playwright API requires every call
    against one browser/page to happen on the same thread, but `BaseScraper.run` calls
    `_fetch_listing_page` from its own loop thread and `_fetch_detail_fields` from a
    separate detail-worker pool - without this they'd fight over the same page from
    two threads at once."""

    @property
    def name(self) -> ScraperName:
        return ScraperName.WELLFOUND

    @property
    def page_size(self) -> int:
        return 1

    @property
    def detail_worker_count(self) -> int:
        # Detail fetches are real page navigations funnelled through the one Playwright
        # thread anyway - more external worker threads would only queue up, not add
        # throughput.
        return 1

    def __init__(self):
        super().__init__()
        self._has_next_page = True
        self._browser_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='wellfound-browser')
        self._run_on_browser_thread(self._start_browser)

    def _run_on_browser_thread(self, fn, *args, **kwargs):
        return self._browser_executor.submit(fn, *args, **kwargs).result()

    def _start_browser(self) -> None:
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)
        self._context = self._browser.new_context()
        self._page = self._context.new_page()
        atexit.register(self._shutdown_browser)
        self._login()

    def _shutdown_browser(self) -> None:
        try:
            self._browser.close()
            self._playwright.stop()
        except Exception:  # noqa: BLE001 - best-effort cleanup on interpreter exit
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

    def _sort_by_most_recent(self):
        """Selects "Most recent" from the results sort dropdown (defaults to
        "Recommended" each fresh session) and returns the JobSearchResultsX response
        that selection triggers, so callers get the first page already sorted by
        `sortBy: LAST_POSTED` instead of an extra throwaway request."""
        with self._page.expect_response(_is_job_search_response, timeout=RESPONSE_WAIT_TIMEOUT_MS) as response_info:
            self._page.get_by_text('Recommended', exact=True).first.click()
            self._page.wait_for_timeout(300)
            self._page.get_by_text('Most recent', exact=True).first.click()
        return response_info.value

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
            official_id=str(job_id),
            title=clean_text(item.get('title')),
            company_name=clean_text(item.get('_startup_name')),
            location=clean_text(location),
            extra={'job_id': job_id, 'slug': slug},
        )

    def _fetch_listing_page(self, start: int, time_range_hours: int) -> ListingPage:
        return self._run_on_browser_thread(self._fetch_listing_page_on_browser_thread, start, time_range_hours)

    def _fetch_listing_page_on_browser_thread(self, start: int, time_range_hours: int) -> ListingPage:
        if start > MAX_SCROLL_ATTEMPTS:
            self._logger.info('stopping pagination, reached max scroll attempts=%s', MAX_SCROLL_ATTEMPTS)
            return ListingPage(stop=True)
        if start > 0 and not self._has_next_page:
            return ListingPage(stop=True)

        try:
            if start == 0:
                self._page.goto(JOBS_URL, wait_until='load', timeout=NAVIGATION_TIMEOUT_MS)
                response = self._sort_by_most_recent()
            else:
                wait_between_requests()
                with self._page.expect_response(_is_job_search_response, timeout=RESPONSE_WAIT_TIMEOUT_MS) as response_info:
                    self._page.mouse.wheel(0, SCROLL_PX)
                response = response_info.value
        except PlaywrightTimeoutError:
            self._logger.info('stopping pagination, no JobSearchResultsX response after scrolling')
            return ListingPage(stop=True)

        response_json = response.json()
        items = self._parse_list_items(response_json)
        self._has_next_page = bool(
            response_json.get('data', {}).get('talent', {}).get('jobSearchResults', {}).get('hasNextPage')
        )

        cutoff = time.time() - time_range_hours * SECONDS_PER_HOUR
        listings = []
        for item in items:
            live_start_at = item.get('liveStartAt')
            if isinstance(live_start_at, (int, float)) and live_start_at < cutoff:
                continue
            listing = self._map_item_to_listing(item)
            if listing is not None:
                listings.append(listing)

        return ListingPage(listings=listings, stop=not self._has_next_page and not items)

    def _fetch_detail_fields(self, listing: ScraperJobData) -> dict:
        return self._run_on_browser_thread(self._fetch_detail_fields_on_browser_thread, listing)

    def _fetch_detail_fields_on_browser_thread(self, listing: ScraperJobData) -> dict:
        wait_between_requests()
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
