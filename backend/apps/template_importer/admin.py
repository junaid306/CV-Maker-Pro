from django.contrib import admin

from .models import ConversionElement, TemplateImportJob, TemplateImportPage


@admin.register(TemplateImportJob)
class TemplateImportJobAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "status", "page_count", "uploaded_by", "created_at")
    list_filter = ("status",)


admin.site.register([TemplateImportPage, ConversionElement])
