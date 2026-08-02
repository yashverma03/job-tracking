from rest_framework import serializers

from modules.resume.dto.resume_generation_outcome_dto import ResumeGenerationOutcomeDTO


class ResumeGenerationResponseDTO(serializers.Serializer):
    processed = serializers.IntegerField()
    generated = ResumeGenerationOutcomeDTO(many=True)
    failed = ResumeGenerationOutcomeDTO(many=True)
