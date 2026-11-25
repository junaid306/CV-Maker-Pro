from django.conf import settings
from django.db import models


class TemplateCategory(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=60, unique=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "template categories"

    def __str__(self):
        return self.name


class Template(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = ((STATUS_DRAFT, "draft"), (STATUS_PUBLISHED, "published"), (STATUS_ARCHIVED, "archived"))

    name = models.CharField(max_length=120)
    category = models.ForeignKey(TemplateCategory, on_delete=models.PROTECT, related_name="templates")
    layout = models.CharField(max_length=20, default="one-column")  # one-column | two-column
    page_size = models.CharField(max_length=10, default="a4", choices=(("a4", "A4"), ("letter", "Letter")))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT, db_index=True)
    current_version = models.ForeignKey(
        "templates_manager.TemplateVersion", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    usage_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [models.Index(fields=["status", "category"])]

    def __str__(self):
        return self.name


class TemplateVersion(models.Model):
    """Immutable snapshot of a template's JSON definition."""

    template = models.ForeignKey(Template, on_delete=models.CASCADE, related_name="versions")
    version_no = models.PositiveIntegerField(default=1)
    schema_version = models.CharField(max_length=10, default="1.0")
    definition = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-version_no"]
        unique_together = ("template", "version_no")

    def __str__(self):
        return f"{self.template} v{self.version_no}"


class TemplateAsset(models.Model):
    template = models.ForeignKey(Template, on_delete=models.CASCADE, related_name="assets")
    key = models.CharField(max_length=64)
    file = models.FileField(upload_to="templates/%Y/%m/")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("template", "key")


class FavoriteTemplate(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorite_templates")
    template = models.ForeignKey(Template, on_delete=models.CASCADE, related_name="favorited_by")

    class Meta:
        unique_together = ("user", "template")
