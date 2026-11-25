from django.contrib import admin

from .models import AiCostStat, AiFeatureSetting, AiGeneration, AiUsageLog


@admin.register(AiFeatureSetting)
class AiFeatureSettingAdmin(admin.ModelAdmin):
    list_display = ("feature", "enabled", "required_ads", "daily_limit", "provider", "output_tokens")


@admin.register(AiGeneration)
class AiGenerationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "feature", "status", "provider", "created_at")
    exclude = ()


admin.site.register([AiUsageLog, AiCostStat])
