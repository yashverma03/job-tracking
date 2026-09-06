from rest_framework import serializers


class JobScoringQueuedDTO(serializers.Serializer):
    queued = serializers.BooleanField()
    message = serializers.CharField()
