from django.contrib import admin

from .models import AiGenerationCredit, ExportUnlock, RewardFraudLog

admin.site.register([AiGenerationCredit, ExportUnlock, RewardFraudLog])
