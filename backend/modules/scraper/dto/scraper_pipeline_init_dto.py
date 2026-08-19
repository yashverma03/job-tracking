from rest_framework import serializers


class ScraperPipelineInitDTO(serializers.Serializer):
    max_jobs_per_run = serializers.IntegerField(min_value=1, max_value=1000, default=1000)
    start_offset = serializers.IntegerField(min_value=0, default=0)
