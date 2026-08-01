from rest_framework import serializers

from modules.jobs.dto.validators import validate_years_range
from modules.jobs.enums.job_referral_status import JobReferralStatus
from modules.jobs.enums.job_status import JobStatus
from modules.jobs.models import Job


class JobCreateDTO(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=JobStatus.choices, default=JobStatus.TO_APPLY)
    referral_status = serializers.ChoiceField(
        choices=JobReferralStatus.choices, default=JobReferralStatus.NOT_ASKING
    )
    min_years = serializers.DecimalField(
        max_digits=5, decimal_places=2, coerce_to_string=False, required=False, allow_null=True
    )
    max_years = serializers.DecimalField(
        max_digits=5, decimal_places=2, coerce_to_string=False, required=False, allow_null=True
    )

    class Meta:
        model = Job
        fields = [
            'url',
            'secondary_url',
            'referral_status',
            'status',
            'company_name',
            'title',
            'official_id',
            'description',
            'location',
            'min_years',
            'max_years',
            'notes',
        ]
        extra_kwargs = {
            'url': {'required': False, 'allow_blank': True, 'allow_null': True},
            'secondary_url': {'required': False, 'allow_blank': True, 'allow_null': True},
        }

    def validate(self, attrs):
        return validate_years_range(attrs)
