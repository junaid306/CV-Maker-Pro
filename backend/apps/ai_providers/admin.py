from django.contrib import admin

from .models import AiFailoverLog, AiProvider, AiProviderHealthLog


@admin.register(AiProvider)
class AiProviderAdmin(admin.ModelAdmin):
    list_display = ("name", "adapter", "model", "priority", "enabled", "healthy", "has_api_key")
    list_editable = ("priority", "enabled")
    ordering = ("priority",)
    exclude = ("api_key_encrypted",)


admin.site.register([AiProviderHealthLog, AiFailoverLog])
