from abc import ABC, abstractmethod

from modules.scraper.types.scraper_job_data import ScraperJobData


class BaseScraper(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this scraper, matches the value stored in scraper_runs.name."""

    @abstractmethod
    def get_data(self) -> list[ScraperJobData]:
        """Return non-duplicate job postings scraped by this scraper."""

    @abstractmethod
    def get_last_run_metadata(self) -> dict:
        """Return extra stats about the most recent get_data() call, for storage on the scraper run."""
