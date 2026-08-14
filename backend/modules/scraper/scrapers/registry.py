from modules.scraper.base.base_scraper import BaseScraper
from modules.scraper.scrapers.linkedin_scraper import LinkedInScraper


def get_enabled_scrapers() -> list[BaseScraper]:
    return [LinkedInScraper()]
