from django.conf import settings
from django.db import models


class CreditBase(models.Model):
    STATUS_AVAILABLE = "available"
    STATUS_RESERVED = "reserved"
    STATUS_CONSUMED = "consumed"
    STATUS_CHOICES = (
        (STATUS_AVAILABLE, "available"),
        (STATUS_RESERVED, "reserved"),
        (STATUS_CONSUMED, "consumed"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    session = models.ForeignKey("advertisements.AdSession", on_delete=models.PROTECT, related_name="+")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_AVAILABLE, db_index=True)
    granted_at = models.DateTimeField(auto_now_add=True)
    reserved_at = models.DateTimeField(null=True, blank=True)
    consumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True


class AiGenerationCredit(CreditBase):
    feature = models.CharField(max_length=60, blank=True)

    class Meta:
        indexes = [models.Index(fields=["user", "status", "feature"])]


class ExportUnlock(CreditBase):
    purpose = "export"

    class Meta:
        indexes = [models.Index(fields=["user", "status"])]


class RewardFraudLog(models.Model):
    """Duplicate, unsigned or otherwise suspicious reward events."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    transaction_id = models.CharField(max_length=255, blank=True)
    reason = models.CharField(max_length=120)
    detail = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
