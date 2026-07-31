from rest_framework.response import Response
from rest_framework.views import APIView

from modules.jobs.dto import JobCreateDTO, JobListQueryDTO, JobResponseDTO, JobUpdateDTO
from modules.jobs.service import job_service


class JobListCreateView(APIView):
    def get(self, request):
        query_dto = JobListQueryDTO(data=request.query_params)
        query_dto.is_valid(raise_exception=True)
        filters = query_dto.to_filter_params()

        result = job_service.list_jobs(filters)

        return Response({
            'items': JobResponseDTO(result.items, many=True).data,
            'total': result.total,
            'page': result.page,
            'page_size': result.page_size,
        })

    def post(self, request):
        create_dto = JobCreateDTO(data=request.data)
        create_dto.is_valid(raise_exception=True)
        job = job_service.create_job(create_dto.validated_data)
        return Response(JobResponseDTO(job).data, status=201)


class JobDetailView(APIView):
    def get(self, request, job_id):
        job = job_service.get_job(job_id)
        return Response(JobResponseDTO(job).data)

    def patch(self, request, job_id):
        job = job_service.get_job(job_id)
        update_dto = JobUpdateDTO(job, data=request.data, partial=True)
        update_dto.is_valid(raise_exception=True)
        updated_job = job_service.update_job(job_id, update_dto.validated_data)
        return Response(JobResponseDTO(updated_job).data)

    def delete(self, request, job_id):
        job_service.soft_delete_job(job_id)
        return Response(status=204)
