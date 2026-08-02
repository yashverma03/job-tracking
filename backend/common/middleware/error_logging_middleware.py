import logging

logger = logging.getLogger('django.request')


class ErrorLoggingMiddleware:
    """Logs every response with a 4xx/5xx status code, regardless of whether it came
    from a raised exception or a view directly returning an error Response."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if response.status_code >= 400:
            logger.error(
                '%s %s -> %s %s',
                request.method,
                request.get_full_path(),
                response.status_code,
                getattr(response, 'data', ''),
            )

        return response
