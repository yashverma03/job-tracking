from django.db import models


class JobStatus(models.TextChoices):
    TO_APPLY = 'To Apply', 'To Apply'
    APPLIED = 'Applied', 'Applied'
    IN_PROGRESS = 'In Progress', 'In Progress'
    REJECTED = 'Rejected', 'Rejected'
    NOT_CONSIDERING = 'Not considering', 'Not considering'
    OTHER = 'Other', 'Other'
    PENDING = 'Pending', 'Pending'
