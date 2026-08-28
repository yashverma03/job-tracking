from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.scrapers.registry import get_enabled_scrapers
from modules.scraper.services.scraper_pipeline_service import check_and_notify_pipeline_complete, run_scraper


def run_scraper_task(scraper_name: ScraperName, max_jobs_per_run: int, start_offset: int, time_range_hours: int) -> None:
    scraper = next(s for s in get_enabled_scrapers() if s.name == scraper_name)
    run_scraper(scraper, max_jobs_per_run, start_offset, time_range_hours)


def notify_pipeline_complete_task() -> None:
    check_and_notify_pipeline_complete()
