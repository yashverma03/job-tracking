import random
import time

from common.utils.env import get_env_int

MIN_DELAY_MS_ENV_KEY = 'SCRAPER_MIN_DELAY_MS'
MAX_DELAY_MS_ENV_KEY = 'SCRAPER_MAX_DELAY_MS'


def wait_between_requests() -> None:
    min_ms = get_env_int(MIN_DELAY_MS_ENV_KEY)
    max_ms = get_env_int(MAX_DELAY_MS_ENV_KEY)
    time.sleep(random.uniform(min_ms, max_ms) / 1000)
