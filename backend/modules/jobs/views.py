from typing import cast

from djangorestframework_camel_case.util import underscoreize
from rest_framework.response import Response
from rest_framework.views import APIView

from common.utils.dto import validate
from modules.jobs.dto import (
    JobCompanyByUrlQueryDTO,
    JobCreateDTO,
    JobListQueryDTO,
    JobResponseDTO,
    JobSuggestionsQueryDTO,
    JobUpdateDTO,
    MarkUrlSeenDTO,
)
from modules.jobs.services import job_service


class JobListCreateView(APIView):
    def get(self, request):
        query_dto = cast(JobListQueryDTO, JobListQueryDTO(data=underscoreize(request.query_params)))
        validate(query_dto)
        filters = query_dto.to_filter_params()

        result = job_service.list_jobs(filters)

        return Response({
            'items': JobResponseDTO(result.items, many=True).data,
            'total': result.total,
            'page': result.page,
            'page_size': result.page_size,
        })

    def post(self, request):
        data = validate(JobCreateDTO(data=request.data))
        job = job_service.create_job(data)
        return Response(JobResponseDTO(job).data, status=201)


class JobDetailView(APIView):
    def patch(self, request, job_id):
        job = job_service.get_job(job_id)
        data = validate(JobUpdateDTO(job, data=request.data, partial=True))
        updated_job = job_service.update_job(job_id, data)
        return Response(JobResponseDTO(updated_job).data)

    def delete(self, request, job_id):
        job_service.soft_delete_job(job_id)
        return Response(status=204)


class MarkUrlSeenView(APIView):
    def post(self, request):
        data = validate(MarkUrlSeenDTO(data=request.data))
        key = job_service.mark_url_seen(data['url'])
        return Response({'key': key}, status=201)


class CompanyNamesView(APIView):
    def get(self, request):
        data = validate(JobSuggestionsQueryDTO(data=request.query_params))
        return Response(job_service.list_company_names(data.get('search'), data.get('limit')))


class JobTitlesView(APIView):
    def get(self, request):
        data = validate(JobSuggestionsQueryDTO(data=request.query_params))
        return Response(job_service.list_job_titles(data.get('search'), data.get('limit')))


class CompanyByUrlView(APIView):
    def get(self, request):
        data = validate(JobCompanyByUrlQueryDTO(data=request.query_params))
        return Response({'companyName': job_service.get_company_name_by_url(data['url'])})


class JobStatsView(APIView):
    def get(self, request):
        return Response(job_service.get_job_stats())
