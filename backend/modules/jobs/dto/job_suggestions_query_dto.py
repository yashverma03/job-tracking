from rest_framework import serializers


class JobSuggestionsQueryDTO(serializers.Serializer):
    search = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    limit = serializers.IntegerField(required=False, allow_null=True, min_value=1)
