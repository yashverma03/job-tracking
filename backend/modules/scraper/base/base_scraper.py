from abc import ABC, abstractmethod

from modules.company.services import company_service
from modules.jobs.enums.job_referral_status import JobReferralStatus
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.types import ScraperRunResult
from modules.scraper.utils.job_filter import is_location_excluded, is_title_excluded


class BaseScraper(ABC):
    @property
    @abstractmethod
    def name(self) -> ScraperName:
        """Unique identifier for this scraper, matches the value stored in scraper_runs.name."""

    @abstractmethod
    def run(self, max_jobs_per_run: int, start_offset: int, time_range_hours: int) -> ScraperRunResult:
        """Scrape job postings, inserting each non-duplicate one as it is found, and return the run result."""

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
        """Returns the referral status a job should be created with based on the company
        table. Top companies are automatically marked as requiring a referral; every
        other company defaults to not asking."""
        if company_service.is_top_company(company_name):
            return JobReferralStatus.REQUIRED
        return JobReferralStatus.NOT_ASKING
