from django.conf import settings
from django.db import models


class AtsAnalysis(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ats_analyses")
    resume = models.ForeignKey("resumes.Resume", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    uploaded_pdf = models.FileField(upload_to="ats/%Y/%m/", null=True, blank=True)
    total_score = models.PositiveIntegerField(default=0)
    section_scores = models.JSONField(default=dict, blank=True)
    findings = models.JSONField(default=list, blank=True)
    suggestions = models.JSONField(default=list, blank=True)
    missing_keywords = models.JSONField(default=list, blank=True)
    used_ai = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]


class AtsJobDescription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="job_descriptions")
    title = models.CharField(max_length=200, blank=True)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class AtsKeyword(models.Model):
    keyword = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=60, blank=True)
