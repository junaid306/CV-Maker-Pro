from rest_framework import serializers

from apps.templates_manager.models import Template, TemplateCategory


class TemplateCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateCategory
        fields = ("id", "name", "slug")


class TemplateSerializer(serializers.ModelSerializer):
    category = TemplateCategorySerializer(read_only=True)
    definition = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Template
        fields = ("id", "name", "category", "layout", "page_size", "definition", "is_favorite", "usage_count")

    def get_definition(self, obj):
        if obj.current_version:
            return obj.current_version.definition
        return None

    def get_is_favorite(self, obj):
        user = self.context.get("request", None) and getattr(self.context["request"], "user", None)
        if user and user.is_authenticated:
            return obj.favorited_by.filter(user=user).exists()
        return False
