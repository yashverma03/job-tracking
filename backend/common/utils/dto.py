from typing import cast

from rest_framework.serializers import BaseSerializer


def validate(serializer: BaseSerializer) -> dict:
    serializer.is_valid(raise_exception=True)
    return cast(dict, serializer.validated_data)
