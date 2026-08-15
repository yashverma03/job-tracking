from abc import ABC, abstractmethod


class BaseScraper(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this scraper, matches the value stored in scraper_runs.name."""

    @abstractmethod
    def run(self) -> dict:
        """Scrape job postings, inserting each non-duplicate one as it is found, and return run metadata."""
