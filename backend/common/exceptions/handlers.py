from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from common.exceptions.api_exceptions import NotFoundError


def custom_exception_handler(exc, context):
    if isinstance(exc, NotFoundError):
        return Response({'detail': str(exc)}, status=status.HTTP_404_NOT_FOUND)
    return exception_handler(exc, context)
