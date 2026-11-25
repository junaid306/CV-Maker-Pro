from django.contrib import admin

from .models import AdminActivityLog, AppSetting, SystemLog

admin.site.register([AppSetting, AdminActivityLog, SystemLog])
