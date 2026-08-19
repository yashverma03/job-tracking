from curl_cffi.requests.exceptions import RequestException
from tenacity import retry, retry_if_exception_type, retry_if_result, stop_after_attempt, wait_exponential

RETRYABLE_STATUS_CODES = {429, 999}
MAX_GET_RETRIES = 3


def _is_retryable_response(response) -> bool:
    return response.status_code in RETRYABLE_STATUS_CODES or response.status_code >= 500


@retry(
    retry=(retry_if_result(_is_retryable_response) | retry_if_exception_type(RequestException)),
    stop=stop_after_attempt(MAX_GET_RETRIES + 1),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)
def get_with_retry(session, url, **kwargs):
    """GET via the given session, retrying on 429/999/5xx and timeouts/connection errors with exponential backoff."""
    return session.get(url, **kwargs)
