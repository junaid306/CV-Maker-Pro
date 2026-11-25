from django.contrib import admin

from .models import FavoriteTemplate, Template, TemplateAsset, TemplateCategory, TemplateVersion

admin.site.register([TemplateCategory, Template, TemplateVersion, TemplateAsset, FavoriteTemplate])
