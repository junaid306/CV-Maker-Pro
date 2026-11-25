from django.contrib import admin

from .models import Resume, ResumeSection, ResumeVersion

admin.site.register([Resume, ResumeSection, ResumeVersion])
