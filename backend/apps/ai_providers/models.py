from django.db import models


class AiProvider(models.Model):
    """One AI provider configuration. Api keys are stored encrypted at rest."""

    ADAPTER_CHOICES = (
        ("openai", "OpenAI / OpenAI-compatible"),
        ("gemini", "Google Gemini"),
        ("anthropic", "Anthropic Claude"),
    )

    name = models.CharField(max_length=60, unique=True)
    adapter = models.CharField(max_length=20, choices=ADAPTER_CHOICES, default="openai")
    base_url = models.CharField(max_length=255, blank=True)
    model = models.CharField(max_length=120, blank=True)
    api_key_encrypted = models.TextField(blank=True)
    priority = models.PositiveIntegerField(default=10)  # lower = tried first
    enabled = models.BooleanField(default=True)
    is_backup = models.BooleanField(default=False)
    timeout_seconds = models.PositiveIntegerField(default=30)
    max_retries = models.PositiveIntegerField(default=2)
    requests_per_minute = models.PositiveIntegerField(default=60)
    daily_budget_usd = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    monthly_budget_usd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # health / circuit breaker
    healthy = models.BooleanField(default=True)
    consecutive_failures = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)
    opened_until = models.DateTimeField(null=True, blank=True)
    tokens_in = models.BigIntegerField(default=0)
    tokens_out = models.BigIntegerField(default=0)
    cost_usd = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["priority", "id"]

    def __str__(self):
        return f"{self.name} (p{self.priority})"

    @property
    def api_key_decrypted(self):
        from .crypto import decrypt_secret

        if not self.api_key_encrypted:
            raise RuntimeError(f"Provider '{self.name}' has no API key configured.")
        return decrypt_secret(self.api_key_encrypted)

    def set_api_key(self, plain_value):
        from .crypto import encrypt_secret

        self.api_key_encrypted = encrypt_secret(plain_value)

    @property
    def has_api_key(self):
        return bool(self.api_key_encrypted)


class AiProviderHealthLog(models.Model):
    provider = models.ForeignKey(AiProvider, on_delete=models.CASCADE, related_name="health_logs")
    adapter = models.CharField(max_length=20)
    ok = models.BooleanField()
    latency_ms = models.PositiveIntegerField(default=0)
    detail = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class AiFailoverLog(models.Model):
    provider = models.CharField(max_length=60)
    attempt = models.PositiveIntegerField(default=1)
    ok = models.BooleanField()
    status_code = models.PositiveIntegerField(null=True, blank=True)
    error_kind = models.CharField(max_length=60, blank=True)
    retried_next = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
