from dataclasses import dataclass

from modules.scraper.enums.scraper_name import ScraperName


@dataclass
class ScraperRunOutcome:
    """Result of one scraper's run within a pipeline, used to build the pipeline-wide
    summary notification once every scraper has finished."""

    scraper_name: ScraperName
    status: str  # 'success' | 'failed' | 'skipped'
    total_count: int = 0
    total_unique_count: int = 0
    error_count: int = 0
