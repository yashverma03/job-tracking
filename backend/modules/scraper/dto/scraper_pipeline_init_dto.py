from rest_framework import serializers


class ScraperPipelineInitDTO(serializers.Serializer):
    start = serializers.IntegerField(min_value=0, default=0)
    limit = serializers.IntegerField(min_value=1, max_value=1000, default=1000)
