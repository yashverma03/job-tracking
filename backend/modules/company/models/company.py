from django.db import models
from django.db.models.functions import Now

from modules.company.enums.company_type import CompanyType


class Company(models.Model):
    name = models.TextField(unique=True)
    linkedin_url = models.TextField(null=True, blank=True)
    type = models.TextField(choices=CompanyType.choices, null=True, blank=True)
    cooling_period_end_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    career_portal_url = models.TextField(null=True, blank=True)
    referral_type = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_default=Now())
    updated_at = models.DateTimeField(auto_now=True, db_default=Now())
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'companies'

    def __str__(self):
        return self.name
