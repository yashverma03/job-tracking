import threading
from abc import ABC, abstractmethod

from modules.company.services import company_service
from modules.jobs.enums.job_referral_status import JobReferralStatus
from modules.jobs.services import job_service, job_unique_key_service
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.types import ScraperRunResult
from modules.scraper.utils.job_filter import is_location_excluded, is_title_excluded
from modules.scraper.utils.scraper_logger import get_scraper_logger

REQUIRED_LISTING_FIELDS = ('url', 'title', 'company_name', 'location')


class BaseScraper(ABC):
    def __init__(self):
        self._logger = get_scraper_logger(self.name)
        self._state_lock = threading.Lock()
        self._total_unique_count = 0
        self._errors: list[dict] = []

    @property
    @abstractmethod
    def name(self) -> ScraperName:
        """Unique identifier for this scraper, matches the value stored in scraper_runs.name."""

    @abstractmethod
    def run(self, max_jobs_per_run: int, start_offset: int, time_range_hours: int) -> ScraperRunResult:
        """Scrape job postings, inserting each non-duplicate one as it is found, and return the run result."""

    @abstractmethod
    def _fetch_description(self, listing: dict) -> str | None:
        """Fetch the full job description for a listing. Scraper-specific."""

    def _reset_run_state(self) -> None:
        self._total_unique_count = 0
        self._errors = []

    def _record_error(self, url: str | None, message: str) -> None:
        self._logger.warning('job processing failed for %s: %s', url, message)
        with self._state_lock:
            self._errors.append({'url': url, 'message': message})

    def add_job_from_listing(self, listing: dict) -> None:
        """Shared per-listing pipeline every scraper strategy should funnel its listings
        through: de-duplication, required-field validation, the shared exclusion filter,
        fetching the description (scraper-specific), and persisting the job. Only the
        description fetch is scraper-specific; everything else is common business logic."""
        url = listing.get('url')

        if job_unique_key_service.is_duplicate(url, None):
            self._logger.info('duplicate skipped: %s', url)
            return

        missing_fields = [field for field in REQUIRED_LISTING_FIELDS if not listing.get(field)]
        if missing_fields:
            self._record_error(url, f'missing required fields: {", ".join(missing_fields)}')
            return

        if self.is_job_excluded(listing['title'], listing['location'], listing['company_name']):
            self._logger.info('excluded by filter rules: %s', url)
            return

        try:
            self._logger.info('fetching details for %s', url)
            description = self._fetch_description(listing)

            job_service.create_scraped_job(
                title=listing['title'],
                company_name=listing['company_name'],
                location=listing['location'],
                description=description,
                url=listing['url'],
                referral_status=self.get_referral_status_for_company(listing['company_name']),
            )
        except Exception as exc:  # noqa: BLE001 - one job's failure must not abort the run
            self._record_error(url, str(exc))
            return

        with self._state_lock:
            self._total_unique_count += 1
        self._logger.info('job inserted: %s', url)

    def is_job_excluded(self, title: str | None, location: str | None, company_name: str | None) -> bool:
        """Shared pre-insert filter every scraper strategy should apply: excluded role
        titles, out-of-scope locations, blacklisted companies, and companies still in
        their cooling-off period."""
        if is_title_excluded(title):
            return True
        if is_location_excluded(location):
            return True
        if company_service.is_blacklisted(company_name):
            return True
        if company_service.is_in_cooling_period(company_name):
            return True
        return False

    def get_referral_status_for_company(self, company_name: str | None) -> str:
        # if company_service.is_top_company(company_name):
        #     return JobReferralStatus.REQUIRED
        return JobReferralStatus.NOT_ASKING
