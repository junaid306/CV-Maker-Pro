from django.contrib import admin

from .models import AtsAnalysis, AtsJobDescription, AtsKeyword

admin.site.register([AtsAnalysis, AtsJobDescription, AtsKeyword])
