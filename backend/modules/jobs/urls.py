from django.urls import path

from modules.jobs.views import JobDetailView, JobListCreateView, MarkUrlSeenView

urlpatterns = [
    path('jobs', JobListCreateView.as_view(), name='job-list-create'),
    path('jobs/<int:job_id>', JobDetailView.as_view(), name='job-detail'),
    path('jobs/mark-url-seen', MarkUrlSeenView.as_view(), name='job-mark-url-seen'),
]
