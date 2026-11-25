from django.conf import settings
from django.db import models


class PdfExport(models.Model):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    STATUS_CHOICES = ((SUCCEEDED, "succeeded"), (FAILED, "failed"))

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pdf_exports")
    resume = models.ForeignKey("resumes.Resume", on_delete=models.CASCADE, related_name="pdf_exports")
    page_size = models.CharField(max_length=10, default="a4")
    file = models.FileField(upload_to="exports/%Y/%m/", null=True, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=SUCCEEDED)
    error = models.TextField(blank=True)
    unlock = models.ForeignKey("rewards.ExportUnlock", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
