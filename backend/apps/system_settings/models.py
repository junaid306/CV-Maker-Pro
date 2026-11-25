from django.conf import settings
from django.db import models


class AppSetting(models.Model):
    """Key/value configuration store. Admin changes here control backend behavior."""

    key = models.CharField(max_length=100, unique=True, db_index=True)
    value = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    def __str__(self):
        return self.key


DEFAULT_SETTINGS = {
    "maintenance": {"enabled": False, "message": "We are upgrading CV Maker. Please come back soon."},
    "app": {"name": "CV Maker", "support_email": "", "min_app_version": "1.0.0", "force_update": False},
    "ats": {
        "basic_enabled": True,
        "ai_enabled": False,
        "job_match_enabled": True,
        "weights": {
            "contact": 15,
            "summary": 10,
            "experience": 20,
            "education": 15,
            "skills": 15,
            "keywords": 10,
            "formatting": 10,
            "readability": 5,
        },
        "max_upload_mb": 10,
        "analyses_per_day": 5,
    },
    "exports": {"reward_count": 5, "page_size_default": "a4", "max_pages": 10},
}


def get_setting(key, subkey=None, default=None):
    try:
        setting = AppSetting.objects.get(key=key)
    except AppSetting.DoesNotExist:
        setting = None
    if setting is None:
        data = DEFAULT_SETTINGS.get(key, {})
        if subkey is None:
            return data
        return data.get(subkey, default)
    if subkey is None:
        return setting.value
    return setting.value.get(subkey, default)


def set_setting(key, value, user=None):
    setting, _ = AppSetting.objects.update_or_create(key=key, defaults={"value": value, "updated_by": user})
    return setting


class AdminActivityLog(models.Model):
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    action = models.CharField(max_length=200)
    target = models.CharField(max_length=255, blank=True)
    detail = models.JSONField(default=dict, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]


class SystemLog(models.Model):
    LEVELS = (("info", "info"), ("warning", "warning"), ("error", "error"))
    level = models.CharField(max_length=20, choices=LEVELS, default="info")
    source = models.CharField(max_length=100)
    message = models.TextField()
    detail = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
