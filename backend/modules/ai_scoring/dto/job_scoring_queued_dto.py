from rest_framework import serializers


class JobScoringQueuedDTO(serializers.Serializer):
    queued = serializers.BooleanField()
    processing = serializers.IntegerField()
    message = serializers.CharField()
