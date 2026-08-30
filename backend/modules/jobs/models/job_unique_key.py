from django.db import models
from django.db.models.functions import Now


class JobUniqueKey(models.Model):
    key = models.TextField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())
    updated_at = models.DateTimeField(auto_now=True, db_default=Now())

    class Meta:
        db_table = 'job_unique_keys'

    def __str__(self):
        return self.key
