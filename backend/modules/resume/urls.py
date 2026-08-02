from django.urls import path

from modules.resume.views import GenerateResumesView

urlpatterns = [
    path('resumes/generate', GenerateResumesView.as_view(), name='resume-generate'),
]
