from django.urls import path

from modules.jobs.views import JobDetailView, JobListCreateView

urlpatterns = [
    path('jobs', JobListCreateView.as_view(), name='job-list-create'),
    path('jobs/<int:job_id>', JobDetailView.as_view(), name='job-detail'),
]
