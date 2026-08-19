from django.urls import path

from modules.scraper.views import InitScraperPipelineView, TriggerScraperPipelineView

urlpatterns = [
    path('scraper', TriggerScraperPipelineView.as_view(), name='scraper-trigger'),
    path('scraper/init', InitScraperPipelineView.as_view(), name='scraper-init'),
]
