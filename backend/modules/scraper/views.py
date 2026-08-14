from django_q.tasks import async_task
from rest_framework.response import Response
from rest_framework.views import APIView


class TriggerScraperPipelineView(APIView):
    def post(self, request):
        async_task('modules.scraper.tasks.run_scraper_pipeline_task')
        return Response({'message': 'Scraper pipeline started'}, status=202)
