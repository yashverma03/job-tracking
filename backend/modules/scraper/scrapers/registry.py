from modules.scraper.base.base_scraper import BaseScraper
from modules.scraper.scrapers.linkedin_scraper import LinkedInScraper
from modules.scraper.scrapers.microsoft_scraper import MicrosoftScraper


def get_enabled_scrapers() -> list[BaseScraper]:
    return [LinkedInScraper(), MicrosoftScraper()]
