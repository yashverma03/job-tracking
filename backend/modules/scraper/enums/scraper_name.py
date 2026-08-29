from django.db import models


class ScraperName(models.TextChoices):
    LINKEDIN = 'linkedin', 'LinkedIn'
    MICROSOFT = 'Microsoft', 'Microsoft'
    NATWEST = 'NatWest Group', 'NatWest Group'
    ADOBE = 'Adobe', 'Adobe'
    ORACLE = 'Oracle', 'Oracle'
