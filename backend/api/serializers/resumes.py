from rest_framework import serializers

from apps.resumes.models import Resume, ResumeSection


class ResumeSectionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = ResumeSection
        fields = ("id", "key", "title", "order", "data")


class ResumeSerializer(serializers.ModelSerializer):
    sections = ResumeSectionSerializer(many=True, required=False)

    class Meta:
        model = Resume
        fields = ("id", "title", "template", "template_version", "data", "sections",
                  "autosaved_at", "created_at", "updated_at", "is_deleted")
        read_only_fields = ("autosaved_at", "created_at", "updated_at", "is_deleted")


class ResumeWriteSerializer(serializers.ModelSerializer):
    sections = ResumeSectionSerializer(many=True, required=False, write_only=True)
    template_version = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Resume
        fields = ("id", "title", "template", "template_version", "data", "sections")


class ResumeVersionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    note = serializers.CharField()


class ResumeDetailSerializer(ResumeSerializer):
    pass
