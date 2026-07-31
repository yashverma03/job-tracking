from rest_framework.response import Response
from rest_framework.views import exception_handler

from common.exceptions.api_exceptions import ApiError


def custom_exception_handler(exc, context):
    if isinstance(exc, ApiError):
        return Response(
            {'message': exc.message, 'detail': exc.details},
            status=exc.status_code,
        )
    return exception_handler(exc, context)
