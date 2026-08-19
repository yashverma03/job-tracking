from rest_framework.response import Response
from rest_framework.views import APIView

from common.utils.dto import validate
from modules.scraper.dto import ScraperPipelineQueuedDTO, ScraperPipelineTriggerDTO
from modules.scraper.services.scraper_pipeline_service import trigger_scraper_pipeline


class TriggerScraperPipelineView(APIView):
    def post(self, request):
        data = validate(ScraperPipelineTriggerDTO(data=request.data))
        result = trigger_scraper_pipeline(data['max_jobs_per_run'], data['start_offset'])
        status_code = 202 if result['queued'] else 200
        return Response(ScraperPipelineQueuedDTO(result).data, status=status_code)
