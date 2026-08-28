from abc import abstractmethod

from common.utils.http import get_with_retry
from modules.scraper.base.base_scraper import BaseScraper
from modules.scraper.constants import REQUEST_TIMEOUT_SECONDS
from modules.scraper.types import ListingPage, ScraperJobData
from modules.scraper.utils.http_session import new_session
from modules.scraper.utils.rate_limiter import wait_between_requests
from modules.scraper.utils.user_agent_rotator import get_random_user_agent


class ApiScraper(BaseScraper):
    """Optional base for scrapers built on a plain JSON list-endpoint + JSON
    detail-endpoint API - the shape most job-board APIs share (Microsoft's included).
    Turns the repetitive "GET a page, pull items out, map each to a listing; GET a
    job's detail, pull fields out" dance into a handful of small hooks instead of
    hand-rolled HTTP + parsing per scraper.

    Not every scraper should use this: one scraping HTML, needing proxy rotation, or
    shaped some other way is expected to subclass `BaseScraper` directly instead - this
    is a convenience for the common case, not a mandatory layer."""

    def __init__(self):
        super().__init__()
        self._session = new_session()
        self._session.headers['User-Agent'] = get_random_user_agent()

    def _request(self, url: str, **kwargs):
        kwargs.setdefault('timeout', REQUEST_TIMEOUT_SECONDS)
        return get_with_retry(lambda: self._session, url, **kwargs)

    @property
    @abstractmethod
    def list_url(self) -> str:
        """Endpoint returning one page of candidate items."""

    @property
    @abstractmethod
    def detail_url(self) -> str:
        """Endpoint returning the extra fields for a single job."""

    @abstractmethod
    def build_list_params(self, start: int) -> dict:
        """Query params for one page of the list endpoint."""

    @abstractmethod
    def parse_list_items(self, response_json: dict) -> list[dict]:
        """Pull the raw list of item dicts out of the list endpoint's response."""

    @abstractmethod
    def map_item_to_listing(self, item: dict) -> ScraperJobData | None:
        """Map one raw item to a ScraperJobData, or return None to skip it (recording
        an error first via `self._record_error` if the item is malformed)."""

    @abstractmethod
    def build_detail_params(self, listing: ScraperJobData) -> dict:
        """Query params for the detail endpoint for one listing."""

    @abstractmethod
    def parse_detail_fields(self, response_json: dict) -> dict:
        """Pull whatever fields the detail endpoint provides, as a dict to merge onto
        the listing (typically just `description`)."""

    def is_item_in_time_range(self, item: dict, time_range_hours: int) -> bool:
        """Override to filter out stale items using a source-specific timestamp field.
        Defaults to including everything."""
        return True

    def _fetch_listing_page(self, start: int, time_range_hours: int) -> ListingPage:
        response = self._request(self.list_url, params=self.build_list_params(start))
        response.raise_for_status()
        items = self.parse_list_items(response.json())

        if not items:
            self._logger.info('stopping pagination, got an empty page')
            return ListingPage(stop=True)

        listings = []
        for item in items:
            if not self.is_item_in_time_range(item, time_range_hours):
                continue
            listing = self.map_item_to_listing(item)
            if listing is not None:
                listings.append(listing)

        return ListingPage(listings=listings)

    def _fetch_detail_fields(self, listing: ScraperJobData) -> dict:
        wait_between_requests()
        response = self._request(self.detail_url, params=self.build_detail_params(listing))
        response.raise_for_status()
        return self.parse_detail_fields(response.json())
