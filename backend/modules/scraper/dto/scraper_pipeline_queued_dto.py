from rest_framework import serializers


class ScraperPipelineQueuedDTO(serializers.Serializer):
    queued = serializers.BooleanField()
    message = serializers.CharField()
