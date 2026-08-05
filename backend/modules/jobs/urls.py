from django.urls import path

from modules.jobs.views import (
    CompanyByUrlView,
    CompanyNamesView,
    JobDetailView,
    JobListCreateView,
    JobStatsView,
    JobTitlesView,
    MarkUrlSeenView,
)

urlpatterns = [
    path('jobs', JobListCreateView.as_view(), name='job-list-create'),
    path('jobs/company-names', CompanyNamesView.as_view(), name='job-company-names'),
    path('jobs/company-by-url', CompanyByUrlView.as_view(), name='job-company-by-url'),
    path('jobs/job-titles', JobTitlesView.as_view(), name='job-titles'),
    path('jobs/stats', JobStatsView.as_view(), name='job-stats'),
    path('jobs/mark-url-seen', MarkUrlSeenView.as_view(), name='job-mark-url-seen'),
    path('jobs/<int:job_id>', JobDetailView.as_view(), name='job-detail'),
]
