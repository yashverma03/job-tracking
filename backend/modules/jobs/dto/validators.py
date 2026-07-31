from rest_framework import serializers


def validate_years_range(attrs):
    min_years = attrs.get('min_years')
    max_years = attrs.get('max_years')
    if min_years is not None and max_years is not None and min_years > max_years:
        raise serializers.ValidationError(
            {'min_years': 'min_years must not be greater than max_years.'}
        )
    return attrs
