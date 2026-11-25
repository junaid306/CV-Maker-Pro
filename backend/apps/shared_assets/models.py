from django.conf import settings
from django.db import models


class SharedAsset(models.Model):
    """Curated server-wide assets (shared avatars, icons, fonts)."""

    KIND_CHOICES = (("avatar", "Avatar"), ("icon", "Icon"), ("font", "Font"), ("other", "Other"))

    key = models.CharField(max_length=50, unique=True, db_index=True)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default="avatar", db_index=True)
    file = models.FileField(upload_to="shared/%Y/%m/", blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["kind", "key"]

    def __str__(self):
        return self.key


class UserAsset(models.Model):
    """A user profile photo is uploaded once and reused across all their CVs."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assets")
    file = models.FileField(upload_to="users/%Y/%m/")
    thumbnail = models.FileField(upload_to="users/%Y/%m/thumbs/", blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
        indexes = [models.Index(fields=["user", "uploaded_at"], name="shared_asse_user_id_dc40d2_idx")]

    def __str__(self):
        return f"asset#{self.pk} user={self.user_id}"
