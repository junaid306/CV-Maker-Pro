from django.conf import settings
from django.db import models


class Resume(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="resumes")
    template = models.ForeignKey(
        "templates_manager.Template", null=True, blank=True, on_delete=models.SET_NULL, related_name="resumes"
    )
    template_version = models.ForeignKey(
        "templates_manager.TemplateVersion", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    title = models.CharField(max_length=200, default="Untitled CV")
    data = models.JSONField(default=dict, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    # Cloud backup / autosave
    autosaved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [models.Index(fields=["user", "is_deleted"])]

    def __str__(self):
        return f"{self.title} ({self.user})"


class ResumeSection(models.Model):
    """Repeatable section instances (education, experience, ...)."""

    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="sections")
    key = models.CharField(max_length=60)  # education, experience, skills...
    title = models.CharField(max_length=120, blank=True)
    order = models.PositiveIntegerField(default=0)
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]
        unique_together = ("resume", "order", "key")

    def __str__(self):
        return f"{self.resume_id}:{self.key}#{self.order}"


class ResumeVersion(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="versions")
    snapshot = models.JSONField()
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"v@{self.created_at:%Y-%m-%d %H:%M}"
