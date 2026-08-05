from rest_framework import serializers


class JobCompanyByUrlQueryDTO(serializers.Serializer):
    url = serializers.CharField(required=True, allow_blank=False)
