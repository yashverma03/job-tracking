from rest_framework.response import Response
from rest_framework.views import APIView

from modules.ai_scoring.dto import JobScoringQueuedDTO
from modules.ai_scoring.services.job_scoring_service import trigger_job_scoring


class TriggerJobScoringView(APIView):
    def post(self, request):
        result = trigger_job_scoring()
        status_code = 202 if result['queued'] else 200
        return Response(JobScoringQueuedDTO(result).data, status=status_code)
