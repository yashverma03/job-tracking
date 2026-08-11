from django.urls import path

from modules.resume.views import (
    GenerateResumeForJobView,
    GenerateResumesView,
    ResumeFileView,
)

urlpatterns = [
    path('resumes', GenerateResumesView.as_view(), name='resume-generate'),
    path('resumes/<int:job_id>', GenerateResumeForJobView.as_view(), name='resume-for-job'),
    path('resumes/<int:job_id>/file', ResumeFileView.as_view(), name='resume-file'),
]
