from django.urls import path

from modules.ai_scoring.views import TriggerJobScoringView

urlpatterns = [
    path('job-scoring', TriggerJobScoringView.as_view(), name='job-scoring-trigger'),
]
