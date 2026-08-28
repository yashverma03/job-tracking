import time

from modules.scraper.constants import SECONDS_PER_HOUR


def is_within_time_range(posted_ts: int | float | None, time_range_hours: int) -> bool:
    """True if `posted_ts` (a unix timestamp) falls within the last `time_range_hours`.
    A missing timestamp is treated as within range, since it can't be judged stale."""
    if posted_ts is None:
        return True
    cutoff_ts = time.time() - time_range_hours * SECONDS_PER_HOUR
    return posted_ts >= cutoff_ts
