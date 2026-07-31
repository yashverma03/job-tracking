from rest_framework import serializers

from modules.jobs.dto.validators import validate_years_range
from modules.jobs.enums.job_referral_status import JobReferralStatus
from modules.jobs.enums.job_status import JobStatus
from modules.jobs.models import Job


class JobUpdateDTO(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=JobStatus.choices, required=False)
    referral_status = serializers.ChoiceField(choices=JobReferralStatus.choices, required=False)
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
            'url': {'required': False, 'allow_blank': False},
        }

    def validate(self, attrs):
        min_years = attrs.get('min_years', getattr(self.instance, 'min_years', None))
        max_years = attrs.get('max_years', getattr(self.instance, 'max_years', None))
        validate_years_range({'min_years': min_years, 'max_years': max_years})
        return attrs
