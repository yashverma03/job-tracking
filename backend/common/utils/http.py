from curl_cffi.requests.exceptions import RequestException
from tenacity import retry, retry_if_exception_type, retry_if_result, stop_after_attempt, wait_exponential

RETRYABLE_STATUS_CODES = {429, 999}
MAX_GET_RETRIES = 3


def _is_retryable_response(response) -> bool:
    return response.status_code in RETRYABLE_STATUS_CODES or response.status_code >= 500


def get_with_retry(get_session, url, on_retry=None, **kwargs):
    """GET via a session, retrying on 429/999/5xx responses and any request exception (connection
    errors, SSL errors, timeouts, etc. - curl_cffi raises all of these as subclasses of
    RequestException).
   """

    @retry(
        retry=(retry_if_result(_is_retryable_response) | retry_if_exception_type(RequestException)),
        stop=stop_after_attempt(MAX_GET_RETRIES + 1),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        before_sleep=(lambda *_: on_retry()) if on_retry is not None else None,
        reraise=True,
    )
    def _do_request():
        return get_session().get(url, **kwargs)

    return _do_request()


def post_with_retry(get_session, url, on_retry=None, **kwargs):
    """Same retry behavior as `get_with_retry`, for APIs (e.g. Workday) whose list
    endpoint only accepts POST with a JSON body."""

    @retry(
        retry=(retry_if_result(_is_retryable_response) | retry_if_exception_type(RequestException)),
        stop=stop_after_attempt(MAX_GET_RETRIES + 1),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        before_sleep=(lambda *_: on_retry()) if on_retry is not None else None,
        reraise=True,
    )
    def _do_request():
        return get_session().post(url, **kwargs)

    return _do_request()
