from rest_framework import serializers


class JobScoreUpdateDTO(serializers.Serializer):
    score = serializers.ChoiceField(choices=[0, 100])
    analysis = serializers.CharField(allow_blank=True)
