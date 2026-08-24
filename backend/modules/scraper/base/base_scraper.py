from abc import ABC, abstractmethod

from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.types import ScraperRunResult


class BaseScraper(ABC):
    @property
    @abstractmethod
    def name(self) -> ScraperName:
        """Unique identifier for this scraper, matches the value stored in scraper_runs.name."""

    @abstractmethod
    def run(self, max_jobs_per_run: int, start_offset: int, time_range_hours: int) -> ScraperRunResult:
        """Scrape job postings, inserting each non-duplicate one as it is found, and return the run result."""
