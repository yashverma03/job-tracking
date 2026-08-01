from typing import cast

from djangorestframework_camel_case.util import underscoreize
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.jobs.dto import JobCreateDTO, JobListQueryDTO, JobResponseDTO, JobUpdateDTO, MarkUrlSeenDTO
from modules.jobs.services import job_service, job_unique_key_service


class JobListCreateView(APIView):
    def get(self, request):
        query_dto = cast(JobListQueryDTO, JobListQueryDTO(data=underscoreize(request.query_params)))
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
        job = job_service.create_job(cast(dict, create_dto.validated_data))
        return Response(JobResponseDTO(job).data, status=201)


class JobDetailView(APIView):
    def patch(self, request, job_id):
        job = job_service.get_job(job_id)
        update_dto = JobUpdateDTO(job, data=request.data, partial=True)
        update_dto.is_valid(raise_exception=True)
        updated_job = job_service.update_job(job_id, cast(dict, update_dto.validated_data))
        return Response(JobResponseDTO(updated_job).data)

    def delete(self, request, job_id):
        job_service.soft_delete_job(job_id)
        return Response(status=204)


class MarkUrlSeenView(APIView):
    def post(self, request):
        dto = MarkUrlSeenDTO(data=request.data)
        dto.is_valid(raise_exception=True)
        key = job_unique_key_service.mark_url_seen(cast(dict, dto.validated_data)['url'])
        return Response({'key': key}, status=201)
