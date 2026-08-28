from dataclasses import dataclass, field

from modules.scraper.types.scraper_job_data import ScraperJobData


@dataclass
class ListingPage:
    """Result of fetching one page of listings. `stop` tells the base run loop to end
    pagination after this page (e.g. the page was empty, or a scraper-specific
    threshold like too many consecutive empty pages was hit)."""

    listings: list[ScraperJobData] = field(default_factory=list)
    stop: bool = False
