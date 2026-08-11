from rest_framework import serializers


class ResumeGenerationQueuedDTO(serializers.Serializer):
    queued = serializers.BooleanField()
    processing = serializers.IntegerField()
    message = serializers.CharField()
