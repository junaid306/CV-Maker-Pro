from rest_framework import serializers

from apps.ats_checker.models import AtsAnalysis


class AtsTextAnalyzeSerializer(serializers.Serializer):
    text = serializers.CharField()
    job_description = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_text(self, value):
        if len(value.strip()) < 20:
            raise serializers.ValidationError("CV text is too short to analyze.")
        return value


class AtsResumeAnalyzeSerializer(serializers.Serializer):
    resume = serializers.IntegerField()
    job_description = serializers.CharField(required=False, allow_blank=True, default="")


class AtsAnalysisSerializer(serializers.ModelSerializer):
    disclaimer = serializers.SerializerMethodField()

    class Meta:
        model = AtsAnalysis
        fields = ("id", "total_score", "section_scores", "findings", "suggestions", "missing_keywords",
                  "used_ai", "created_at", "disclaimer")

    def get_disclaimer(self, obj):
        return ("This score is an estimated ATS compatibility indicator, not an actual employer ATS "
                "result or a hiring guarantee.")
