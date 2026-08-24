from rest_framework.response import Response
from rest_framework.views import APIView

from common.utils.dto import validate
from modules.scraper.dto import ScraperPipelineInitDTO, ScraperPipelineQueuedDTO, ScraperPipelineTriggerDTO
from modules.scraper.services.scraper_pipeline_service import init_scraper_pipeline, trigger_scraper_pipeline


class TriggerScraperPipelineView(APIView):
    def post(self, request):
        data = validate(ScraperPipelineTriggerDTO(data=request.data))
        result = trigger_scraper_pipeline(data['max_jobs_per_run'], data['start_offset'], data['time_range_hours'])
        status_code = 202 if result['queued'] else 200
        return Response(ScraperPipelineQueuedDTO(result).data, status=status_code)


class InitScraperPipelineView(APIView):
    def post(self, request):
        data = validate(ScraperPipelineInitDTO(data=request.data))
        result = init_scraper_pipeline(data['max_jobs_per_run'], data['start_offset'], data['time_range_hours'])
        status_code = 202 if result['queued'] else 200
        return Response(ScraperPipelineQueuedDTO(result).data, status=status_code)
