from django.db import models


class AdSetting(models.Model):
    singleton = models.PositiveSmallIntegerField(default=1, unique=True)
    app_open_enabled = models.BooleanField(default=True)
    app_open_skip_first_launch = models.BooleanField(default=True)
    app_open_max_per_day = models.PositiveIntegerField(default=0)  # 0 = unlimited
    native_dashboard_enabled = models.BooleanField(default=True)
    native_gallery_enabled = models.BooleanField(default=True)
    banner_enabled = models.BooleanField(default=False)
    rewarded_enabled = models.BooleanField(default=True)
    test_mode = models.BooleanField(default=True)
    ad_unit_ids = models.JSONField(default=dict, blank=True)  # placement -> unit id
    ssv_key_id = models.CharField(max_length=64, blank=True)
    ssv_public_key_pem = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ad settings"
        verbose_name_plural = "ad settings"

    def __str__(self):
        return "Ad Settings"

    @classmethod
    def load(cls):
        return cls.objects.filter(pk=1).first() or cls.objects.create(pk=1)


class AdRewardRequirement(models.Model):
    PURPOSE_AI = "ai"
    PURPOSE_EXPORT = "export"
    PURPOSE_CHOICES = ((PURPOSE_AI, "AI generation"), (PURPOSE_EXPORT, "PDF export"))

    purpose = models.CharField(max_length=20, unique=True, choices=PURPOSE_CHOICES)
    required_ads = models.PositiveIntegerField(default=5)
    enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.purpose}: {self.required_ads} ads"


class AdSession(models.Model):
    """One reward-earning session for a purpose (user watches N rewarded ads)."""

    STATUS_OPEN = "open"
    STATUS_COMPLETED = "completed"
    STATUS_CHOICES = ((STATUS_OPEN, "open"), (STATUS_COMPLETED, "completed"))

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="ad_sessions")
    purpose = models.CharField(max_length=20, choices=AdRewardRequirement.PURPOSE_CHOICES)
    feature = models.CharField(max_length=60, blank=True)  # AI feature key, if purpose == ai
    required_count = models.PositiveIntegerField(default=5)
    verified_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_OPEN, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "purpose", "status"])]

    def __str__(self):
        return f"session#{self.pk} {self.user_id} {self.purpose} {self.verified_count}/{self.required_count}"


class AdReward(models.Model):
    """A single SSV-verified rewarded ad event. transaction_id is unique."""

    session = models.ForeignKey(AdSession, on_delete=models.CASCADE, related_name="rewards", null=True, blank=True)
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="ad_rewards")
    purpose = models.CharField(max_length=20, default="ai")
    transaction_id = models.CharField(max_length=255, unique=True, db_index=True)
    ad_unit = models.CharField(max_length=120, blank=True)
    raw_params = models.JSONField(default=dict, blank=True)
    verified = models.BooleanField(default=False)
    credited_to_session = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "purpose"])]
