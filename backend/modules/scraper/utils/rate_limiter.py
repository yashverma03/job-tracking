import random
import time

MIN_DELAY_SECONDS = 2.0
MAX_DELAY_SECONDS = 5.0


def wait_between_requests(min_seconds: float = MIN_DELAY_SECONDS, max_seconds: float = MAX_DELAY_SECONDS) -> None:
    time.sleep(random.uniform(min_seconds, max_seconds))
