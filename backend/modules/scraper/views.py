from rest_framework.response import Response
from rest_framework.views import APIView

from common.utils.dto import validate
from modules.scraper.dto import ScraperNameOptionDTO, ScraperPipelineQueuedDTO, ScraperPipelineTriggerDTO
from modules.scraper.enums.scraper_name import ScraperName
from modules.scraper.services.scraper_pipeline_service import trigger_scraper_pipeline


class TriggerScraperPipelineView(APIView):
    def get(self, request):
        options = [{'value': value, 'label': label} for value, label in ScraperName.choices]
        return Response(ScraperNameOptionDTO(options, many=True).data)

    def post(self, request):
        data = validate(ScraperPipelineTriggerDTO(data=request.data))

        result = trigger_scraper_pipeline(
            data.get('scraper_names'),
            init_only=data.get('init_only', False),
            run_scoring=data.get('run_scoring', False),
        )
        status_code = 202 if result['queued'] else 200
        return Response(ScraperPipelineQueuedDTO(result).data, status=status_code)
