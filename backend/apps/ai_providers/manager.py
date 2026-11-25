"""AI request routing with automatic failover, circuit breaker and budgets."""
import logging
import time
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .adapters import AdapterError, TransientError, get_adapter
from .models import AiFailoverLog, AiProvider, AiProviderHealthLog

logger = logging.getLogger(__name__)

BREAKER_THRESHOLD = 3
BREAKER_COOLDOWN_SECONDS = 60

BUDGET_EXCEEDED = "budget-exceeded"


class NoProviderAvailable(Exception):
    pass


class GenerationFailed(Exception):
    pass


@transaction.atomic
def _budget_exceeded(provider):
    from apps.ai_tools.models import AiCostStat

    provider = AiProvider.objects.select_for_update().get(pk=provider.pk)
    today = timezone.now().date()
    spent_day = AiCostStat.total_for(provider, day=today)
    if provider.daily_budget_usd is not None and spent_day >= float(provider.daily_budget_usd):
        return True
    month = today.replace(day=1)
    spent_month = AiCostStat.total_for(provider, since=month)
    if provider.monthly_budget_usd is not None and spent_month >= float(provider.monthly_budget_usd):
        return True
    return False


def _record_success(provider, tokens_in, tokens_out, cost_usd, latency_ms):
    AiProvider.objects.filter(pk=provider.pk).update(
        healthy=True, consecutive_failures=0, last_error="",
        opened_until=None,
        tokens_in=provider.tokens_in + tokens_in,
        tokens_out=provider.tokens_out + tokens_out,
    )
    AiProviderHealthLog.objects.create(
        provider=provider, adapter=provider.adapter, ok=True, latency_ms=latency_ms
    )
    if cost_usd:
        from apps.ai_tools.models import AiCostStat

        AiCostStat.record(provider=provider, cost_usd=cost_usd, tokens_in=tokens_in, tokens_out=tokens_out)


def _record_failure(provider, error, retried_next):
    consecutive = provider.consecutive_failures + 1
    updates = {
        "consecutive_failures": consecutive,
        "last_error": str(error)[:2000],
    }
    if consecutive >= BREAKER_THRESHOLD:
        updates["healthy"] = False
        updates["opened_until"] = timezone.now() + timedelta(seconds=BREAKER_COOLDOWN_SECONDS)
    AiProvider.objects.filter(pk=provider.pk).update(**updates)
    AiProviderHealthLog.objects.create(provider=provider, adapter=provider.adapter, ok=False, detail=str(error)[:300])


def _candidate_providers():
    now = timezone.now()
    providers = [
        p for p in AiProvider.objects.all()
        if p.enabled and p.has_api_key and (not p.opened_until or p.opened_until <= now)
    ]
    return sorted(providers, key=lambda p: (p.priority, p.is_backup, p.pk))


def generate_with_failover(prompt, system=None, max_tokens=512, temperature=0.7):
    """Route a prompt through providers in priority order.

    Transient errors move to the next provider; input/credential/safety errors
    abort immediately without blindly retrying every provider.
    """
    attempts = _candidate_providers()
    if not attempts:
        raise NoProviderAvailable("No enabled AI provider with a configured API key is available.")
    last_error = None
    for index, provider in enumerate(attempts):
        for per_provider_try in range(1, provider.max_retries + 1):
            if _budget_exceeded(provider):
                AiFailoverLog.objects.create(
                    provider=provider.name, attempt=per_provider_try, ok=False,
                    error_kind=BUDGET_EXCEEDED, retried_next=True,
                )
                last_error = GenerationFailed(f"Provider '{provider.name}' exceeded its budget.")
                break
            try:
                result = get_adapter(provider).generate(
                    prompt, system=system, max_tokens=max_tokens, temperature=temperature
                )
            except AdapterError as exc:
                _record_failure(provider, exc, retried_next=False)
                AiFailoverLog.objects.create(
                    provider=provider.name, attempt=per_provider_try, ok=False,
                    error_kind="adapter", retried_next=False,
                )
                raise GenerationFailed(str(exc)) from exc
            except TransientError as exc:
                last_error = exc
                retried_next = per_provider_try >= provider.max_retries
                _record_failure(provider, exc, retried_next)
                AiFailoverLog.objects.create(
                    provider=provider.name, attempt=per_provider_try, ok=False,
                    error_kind="transient", retried_next=retried_next,
                )
                if not retried_next:
                    time.sleep(min(2 ** per_provider_try, 8))  # bounded exponential backoff
                continue
            _record_success(provider, result["tokens_in"], result["tokens_out"], 0.0, result["latency_ms"])
            result["provider"] = provider.name
            return result
    raise GenerationFailed(f"All providers failed. Last error: {last_error}")
