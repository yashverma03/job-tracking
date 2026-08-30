from django.db import models


class CompanyType(models.TextChoices):
    TOP_COMPANY = 'topCompany', 'Top company'
    BLACKLIST = 'blacklist', 'Blacklist'
    NORMAL = 'normal', 'Normal'
