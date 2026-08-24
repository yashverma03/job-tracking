from modules.scraper.services.scraper_pipeline_service import run_pipeline


def run_scraper_pipeline_task(max_jobs_per_run: int, start_offset: int, time_range_hours: int) -> None:
    run_pipeline(max_jobs_per_run, start_offset, time_range_hours)
