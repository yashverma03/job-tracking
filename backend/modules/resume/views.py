from rest_framework.response import Response
from rest_framework.views import APIView

from modules.resume.dto import ResumeGenerationOutcomeDTO, ResumeGenerationResponseDTO
from modules.resume.services.resume_generation_service import (
    generate_resume_for_job,
    generate_resumes_for_pending_jobs,
)


class GenerateResumesView(APIView):
    def post(self, request):
        result = generate_resumes_for_pending_jobs()
        return Response(ResumeGenerationResponseDTO(result).data)


class GenerateResumeForJobView(APIView):
    def post(self, request, job_id):
        outcome = generate_resume_for_job(job_id)
        return Response(ResumeGenerationOutcomeDTO(outcome).data)
