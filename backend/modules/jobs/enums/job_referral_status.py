from django.db import models


class JobReferralStatus(models.TextChoices):
    NOT_ASKING = 'Not asking', 'Not asking'
    REQUIRED = 'Referral required', 'Referral required'
    ASKED = 'Referral asked', 'Referral asked'
    GOT = 'Referral got', 'Referral got'
    OTHER = 'Other', 'Other'
