from django.conf import settings
from django.db import models


class TemplateImportJob(models.Model):
    STATUS_UPLOADED = "uploaded"
    STATUS_PROCESSING = "processing"
    STATUS_REVIEW = "needs_review"
    STATUS_FAILED = "failed"
    STATUS_PUBLISHED = "published"
    STATUS_CHOICES = (
        (STATUS_UPLOADED, "uploaded"),
        (STATUS_PROCESSING, "processing"),
        (STATUS_REVIEW, "needs_review"),
        (STATUS_FAILED, "failed"),
        (STATUS_PUBLISHED, "published"),
    )

    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="import_jobs")
    source_pdf = models.FileField(upload_to="imports/%Y/%m/")
    name = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_UPLOADED, db_index=True)
    page_count = models.PositiveIntegerField(default=0)
    warnings = models.JSONField(default=list, blank=True)
    errors = models.JSONField(default=list, blank=True)
    generated_template = models.ForeignKey(
        "templates_manager.TemplateVersion", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    published_template = models.ForeignKey(
        "templates_manager.Template", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    preview_png = models.FileField(upload_to="imports/%Y/%m/previews/", null=True, blank=True)
    ocr_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class TemplateImportPage(models.Model):
    job = models.ForeignKey(TemplateImportJob, on_delete=models.CASCADE, related_name="pages")
    page_no = models.PositiveIntegerField(default=1)
    width = models.FloatField(default=0)
    height = models.FloatField(default=0)
    is_scanned = models.BooleanField(default=False)
    extracted_text = models.TextField(blank=True)


class ConversionElement(models.Model):
    """One extracted element of a conversion, kept for admin correction UI."""

    job = models.ForeignKey(TemplateImportJob, on_delete=models.CASCADE, related_name="elements")
    page_no = models.PositiveIntegerField(default=1)
    element_json = models.JSONField()
    confidence = models.FloatField(default=1.0)
    needs_review = models.BooleanField(default=False)


STATUS = TemplateImportJob.STATUS_CHOICES  # re-export convenience
