from django.conf import settings
from django.db import models

FEATURE_KEYS = (
    "career_objective",
    "professional_summary",
    "experience_bullets",
    "skills_suggestions",
    "education_improver",
    "project_description",
    "grammar_correction",
    "content_improvement",
    "cover_letter",
    "keyword_match",
    "ats_ai_analysis",
    "language_improvement",
)


class AiFeatureSetting(models.Model):
    feature = models.CharField(max_length=60, unique=True, db_index=True)
    enabled = models.BooleanField(default=True)
    required_ads = models.PositiveIntegerField(null=True, blank=True)  # falls back to global
    daily_limit = models.PositiveIntegerField(default=10)
    provider = models.ForeignKey("ai_providers.AiProvider", null=True, blank=True, on_delete=models.SET_NULL)
    model = models.CharField(max_length=120, blank=True)
    input_limit = models.PositiveIntegerField(default=4000)
    output_tokens = models.PositiveIntegerField(default=512)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AI feature {self.feature}"


class AiGeneration(models.Model):
    STATUS_PENDING = "pending"
    STATUS_SUCCEEDED = "succeeded"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = ((STATUS_PENDING, "pending"), (STATUS_SUCCEEDED, "succeeded"), (STATUS_FAILED, "failed"))

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_generations")
    feature = models.CharField(max_length=60)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    input_text = models.TextField(blank=True)
    output_text = models.TextField(blank=True)
    provider = models.CharField(max_length=60, blank=True)
    tokens_in = models.PositiveIntegerField(default=0)
    tokens_out = models.PositiveIntegerField(default=0)
    error = models.TextField(blank=True)
    applied_to_resume = models.ForeignKey(
        "resumes.Resume", null=True, blank=True, on_delete=models.SET_NULL, related_name="ai_generations"
    )
    credit = models.ForeignKey("rewards.AiGenerationCredit", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    idempotency_key = models.CharField(max_length=64, blank=True, db_index=True)
    latency_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "feature", "status"])]


class AiUsageLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    generation = models.ForeignKey(AiGeneration, null=True, on_delete=models.SET_NULL, related_name="+")
    provider = models.CharField(max_length=60)
    feature = models.CharField(max_length=60)
    ok = models.BooleanField(default=True)
    detail = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class AiCostStat(models.Model):
    """Daily aggregate cost per provider, used for budget checks."""

    provider = models.ForeignKey("ai_providers.AiProvider", on_delete=models.CASCADE, related_name="cost_stats")
    day = models.DateField(db_index=True)
    cost_usd = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    tokens_in = models.BigIntegerField(default=0)
    tokens_out = models.BigIntegerField(default=0)

    class Meta:
        unique_together = ("provider", "day")
        ordering = ["-day"]

    @classmethod
    def total_for(cls, provider, day=None, since=None):
        query = cls.objects.filter(provider=provider)
        if day:
            query = query.filter(day=day)
        if since:
            query = query.filter(day__gte=since)
        aggregate = query.aggregate(total=models.Sum("cost_usd"))
        return float(aggregate["total"] or 0)

    @classmethod
    def record(cls, provider, cost_usd, tokens_in=0, tokens_out=0):
        stat, _ = cls.objects.get_or_create(provider=provider, day=timezone_now_date())
        from django.db.models import F

        stat.cost_usd = F("cost_usd") + cost_usd
        stat.tokens_in = F("tokens_in") + tokens_in
        stat.tokens_out = F("tokens_out") + tokens_out
        stat.save(update_fields=["cost_usd", "tokens_in", "tokens_out"])


def timezone_now_date():
    from django.utils import timezone

    return timezone.now().date()
