from rest_framework.response import Response
from rest_framework.views import APIView

from modules.scraper.dto import ScraperPipelineQueuedDTO
from modules.scraper.services.scraper_pipeline_service import trigger_scraper_pipeline


class TriggerScraperPipelineView(APIView):
    def post(self, request):
        result = trigger_scraper_pipeline()
        status_code = 202 if result['queued'] else 200
        return Response(ScraperPipelineQueuedDTO(result).data, status=status_code)
