"""AI generation flow: settings check -> credit reserve -> generate -> settle."""
from django.db.models import Count
from django.utils import timezone

from apps.ai_providers.manager import GenerationFailed, NoProviderAvailable, generate_with_failover
from apps.rewards.services import reserve_ai_credit, settle_credit

from .models import AiFeatureSetting, AiGeneration, AiUsageLog
from .prompts import FEATURE_SYSTEM_PROMPTS, FEATURE_USER_TEMPLATES, INTEGRITY_RULES


def get_feature_setting(feature):
    return AiFeatureSetting.objects.filter(feature=feature).first()


def is_feature_enabled(feature):
    setting = get_feature_setting(feature)
    return bool(setting and setting.enabled)


def generations_today(user, feature):
    start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return AiGeneration.objects.filter(user=user, feature=feature, created_at__gte=start).count()


def required_ads(feature):
    setting = get_feature_setting(feature)
    if setting and setting.required_ads:
        return setting.required_ads
    from apps.rewards.services import get_requirement

    return get_requirement("ai").required_ads


class FeatureDisabled(Exception):
    pass


class DailyLimitReached(Exception):
    pass


class AiRuntimeError(Exception):
    pass


def run_generation(user, feature, input_text="", role="", idempotency_key=None):
    """Full flow. Raises FeatureDisabled / DailyLimitReached / AiRuntimeError."""
    setting = get_feature_setting(feature)
    if not setting or not setting.enabled:
        raise FeatureDisabled("This AI feature is disabled by the administrator.")
    if not input_text:
        raise AiRuntimeError("Input text is required.")
    input_text = input_text[: setting.input_limit]
    if generations_today(user, feature) >= setting.daily_limit:
        raise DailyLimitReached("Daily generation limit reached for this feature.")

    generation = AiGeneration.objects.create(
        user=user, feature=feature, input_text=input_text, status=AiGeneration.STATUS_PENDING,
        idempotency_key=idempotency_key or "",
    )

    credit = reserve_ai_credit(user, feature)
    if credit is None:
        generation.status = AiGeneration.STATUS_FAILED
        generation.error = "No AI credit available. Complete the required rewarded ads first."
        generation.save(update_fields=["status", "error"])
        raise AiRuntimeError(generation.error)

    from apps.rewards.models import AiGenerationCredit

    credit = AiGenerationCredit.objects.select_related(None).get(pk=credit.pk)
    generation.credit = credit
    generation.save(update_fields=["credit"])

    prompt = (FEATURE_USER_TEMPLATES.get(feature) or "{input}").format(role=role or "any", input=input_text)
    system = (FEATURE_SYSTEM_PROMPTS.get(feature) or "You are a CV writing assistant.") + " " + INTEGRITY_RULES
    max_tokens = setting.output_tokens
    try:
        result = generate_with_failover(prompt, system=system, max_tokens=max_tokens)
    except (NoProviderAvailable, GenerationFailed) as exc:
        generation.status = AiGeneration.STATUS_FAILED
        generation.error = str(exc)
        generation.save(update_fields=["status", "error"])
        AiUsageLog.objects.create(user=user, generation=generation, provider="-", feature=feature, ok=False, detail={"error": str(exc)})
        settle_credit(AiGenerationCredit, credit, success=False)
        raise AiRuntimeError(str(exc)) from exc

    generation.output_text = result["text"]
    generation.provider = result.get("provider", "")
    generation.tokens_in = result.get("tokens_in", 0)
    generation.tokens_out = result.get("tokens_out", 0)
    generation.latency_ms = result.get("latency_ms", 0)
    generation.status = AiGeneration.STATUS_SUCCEEDED
    generation.save(update_fields=["output_text", "provider", "tokens_in", "tokens_out", "latency_ms", "status"])
    AiUsageLog.objects.create(user=user, generation=generation, provider=generation.provider, feature=feature, ok=True)
    settle_credit(AiGenerationCredit, credit, success=True)
    return generation
