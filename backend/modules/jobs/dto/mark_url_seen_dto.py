from rest_framework import serializers


class MarkUrlSeenDTO(serializers.Serializer):
    url = serializers.CharField(required=True, allow_blank=False)
