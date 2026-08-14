from django.urls import path

from modules.scraper.views import TriggerScraperPipelineView

urlpatterns = [
    path('scraper', TriggerScraperPipelineView.as_view(), name='scraper-trigger'),
]
