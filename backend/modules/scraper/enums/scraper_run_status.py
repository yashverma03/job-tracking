from django.db import models


class ScraperRunStatus(models.TextChoices):
    PENDING = 'Pending', 'Pending'
    PROCESSING = 'Processing', 'Processing'
    SUCCESS = 'Success', 'Success'
    FAILED = 'Failed', 'Failed'
