from rest_framework import serializers

from modules.scraper.enums.scraper_name import ScraperName


class ScraperPipelineTriggerDTO(serializers.Serializer):
    scraper_names = serializers.ListField(
        child=serializers.ChoiceField(choices=ScraperName.choices), required=False, allow_null=True
    )
