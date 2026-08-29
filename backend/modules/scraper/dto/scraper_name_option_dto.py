from rest_framework import serializers


class ScraperNameOptionDTO(serializers.Serializer):
    value = serializers.CharField()
    label = serializers.CharField()
