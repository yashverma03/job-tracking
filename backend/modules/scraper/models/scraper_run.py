from typing import cast

from django.db import models

from modules.scraper.enums.scraper_run_status import ScraperRunStatus


class ScraperRun(models.Model):
    id: int
    name = models.TextField()
    status = models.TextField(choices=ScraperRunStatus.choices, default=ScraperRunStatus.PENDING)
    error: dict | None = cast('dict | None', models.JSONField(null=True, blank=True))
    metadata: dict | None = cast('dict | None', models.JSONField(null=True, blank=True))
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'scraper_runs'

    def __str__(self):
        return f'{self.name} ({self.status})'
