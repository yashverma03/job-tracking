from django.db import models


class JobUniqueKey(models.Model):
    key = models.TextField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'job_unique_keys'

    def __str__(self):
        return self.key
