import importlib
import pkgutil
from typing import TypeVar

from modules.scraper.base.base_scraper import BaseScraper

_PACKAGE_NAME = __name__.rpartition('.')[0]

_registered_scrapers: list[type[BaseScraper]] = []

ScraperT = TypeVar('ScraperT', bound=BaseScraper)


def register_scraper(scraper_cls: type[ScraperT]) -> type[ScraperT]:
    """Class decorator: adding `@register_scraper` above a new BaseScraper subclass is
    the only step needed to wire it into the pipeline - no separate list to update."""
    _registered_scrapers.append(scraper_cls)
    return scraper_cls


def _import_all_scraper_modules() -> None:
    package = importlib.import_module(_PACKAGE_NAME)
    for module_info in pkgutil.iter_modules(package.__path__):
        if module_info.name != 'registry':
            importlib.import_module(f'{_PACKAGE_NAME}.{module_info.name}')


def get_enabled_scrapers() -> list[BaseScraper]:
    _import_all_scraper_modules()
    return [scraper_cls() for scraper_cls in _registered_scrapers]
