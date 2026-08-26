from rest_framework import serializers


class ScraperPipelineTriggerDTO(serializers.Serializer):
    max_jobs_per_run = serializers.IntegerField(min_value=1, max_value=1000)
    start_offset = serializers.IntegerField(min_value=0)
    time_range_hours = serializers.IntegerField(min_value=1, max_value=168, default=28)
