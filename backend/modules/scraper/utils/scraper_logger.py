import logging
from pathlib import Path

from django.conf import settings

LOG_DIR = Path(settings.BASE_DIR).parent.parent / 'logs'

_loggers: dict[str, logging.Logger] = {}


def get_scraper_logger(name: str) -> logging.Logger:
    if name in _loggers:
        return _loggers[name]

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(f'scraper.{name}')
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.FileHandler(LOG_DIR / f'scraper-{name}.log')
        handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s'))
        logger.addHandler(handler)

    _loggers[name] = logger
    return logger
