from django.urls import path

from modules.jobs.views import (
    CompanyNamesView,
    JobDetailView,
    JobListCreateView,
    JobTitlesView,
    MarkUrlSeenView,
)

urlpatterns = [
    path('jobs', JobListCreateView.as_view(), name='job-list-create'),
    path('jobs/company-names', CompanyNamesView.as_view(), name='job-company-names'),
    path('jobs/job-titles', JobTitlesView.as_view(), name='job-titles'),
    path('jobs/mark-url-seen', MarkUrlSeenView.as_view(), name='job-mark-url-seen'),
    path('jobs/<int:job_id>', JobDetailView.as_view(), name='job-detail'),
]
