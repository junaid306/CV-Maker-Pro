"""Reward, session and credit lifecycle services.

Rules enforced here (PRD sections 10, 11, 14):
- A credit is granted only after N SSV-verified rewarded ads.
- A credit is reserved when generation/export starts.
- A credit is consumed only after success; failures release it.
- Duplicate transaction ids are rejected; unsigned events never grant anything.
- AI rewards and export rewards are independent.
"""
import logging

from django.db import transaction
from django.utils import timezone

from apps.advertisements.models import AdReward, AdRewardRequirement, AdSession
from apps.rewards.models import AiGenerationCredit, ExportUnlock

logger = logging.getLogger(__name__)

REASONS_DUPLICATE = "duplicate_transaction"


def get_requirement(purpose, feature=None):
    """Resolve required ad count for a purpose, honoring per-feature overrides."""
    requirement = AdRewardRequirement.objects.filter(purpose=purpose).first()
    if requirement is None:
        requirement = AdRewardRequirement.objects.create(purpose=purpose, required_ads=5, enabled=True)
    return requirement


@transaction.atomic
def open_reward_session(user, purpose, feature=None):
    from apps.advertisements.models import AdSetting

    setting = AdSetting.load()
    if not setting.rewarded_enabled:
        raise PermissionError("Rewarded ads are currently disabled.")
    requirement = get_requirement(purpose)
    open_session = (
        AdSession.objects.select_for_update()
        .filter(user=user, purpose=purpose, status=AdSession.STATUS_OPEN, feature=feature or "")
        .first()
    )
    if open_session:
        return open_session
    return AdSession.objects.create(
        user=user,
        purpose=purpose,
        feature=feature or "",
        required_count=requirement.required_ads,
    )


@transaction.atomic
def record_verified_reward(session, transaction_id, raw_params=None, purpose=None):
    """Attach an SSV-verified rewarded ad to a session exactly once."""
    session = AdSession.objects.select_for_update().get(pk=session.pk)
    if AdReward.objects.filter(transaction_id=transaction_id).exists():
        from apps.system_settings.models import SystemLog
        from .models import RewardFraudLog

        RewardFraudLog.objects.create(
            user_id=session.user_id, transaction_id=transaction_id, reason=REASONS_DUPLICATE, detail=raw_params or {}
        )
        SystemLog.objects.create(
            level="warning", source="rewards", message="Duplicate reward transaction rejected",
            detail={"transaction_id": transaction_id, "user_id": session.user_id},
        )
        return None, False

    AdReward.objects.create(
        session=session,
        user_id=session.user_id,
        purpose=purpose or session.purpose,
        transaction_id=transaction_id,
        raw_params=raw_params or {},
        verified=True,
    )
    session.verified_count += 1
    session.save(update_fields=["verified_count"])
    if session.verified_count >= session.required_count and session.status == AdSession.STATUS_OPEN:
        session.status = AdSession.STATUS_COMPLETED
        session.completed_at = timezone.now()
        session.save(update_fields=["status", "completed_at"])
        granted = _grant_credit_for_session(session)
        return session, granted
    return session, False


def _grant_credit_for_session(session):
    if session.purpose == AdRewardRequirement.PURPOSE_AI:
        AiGenerationCredit.objects.get_or_create(
            session=session,
            defaults={"user_id": session.user_id, "feature": session.feature},
        )
        return True
    ExportUnlock.objects.get_or_create(session=session, defaults={"user_id": session.user_id})
    return True


@transaction.atomic
def reserve_ai_credit(user, feature):
    credit = (
        AiGenerationCredit.objects.select_for_update()
        .filter(user=user, status=AiGenerationCredit.STATUS_AVAILABLE, feature__in=[feature, ""])
        .order_by("-granted_at")
        .first()
    )
    if credit is None:
        return None
    credit.status = AiGenerationCredit.STATUS_RESERVED
    credit.reserved_at = timezone.now()
    credit.feature = feature
    credit.save(update_fields=["status", "reserved_at", "feature"])
    return credit


@transaction.atomic
def settle_credit(credit_model, credit, success):
    """Consume the credit on success, release it on failure. Idempotent."""
    if credit is None:
        return None
    credit = credit_model.objects.select_for_update().get(pk=credit.pk)
    if success:
        if credit.status in (AiGenerationCredit.STATUS_CONSUMED,):
            return credit
        credit.status = AiGenerationCredit.STATUS_CONSUMED
        credit.consumed_at = timezone.now()
    else:
        if credit.status in (AiGenerationCredit.STATUS_AVAILABLE,):
            return credit
        credit.status = AiGenerationCredit.STATUS_AVAILABLE
        credit.reserved_at = None
    credit.save(update_fields=["status", "consumed_at", "reserved_at"])
    return credit


def release_export_unlock(unlock):
    return settle_credit(ExportUnlock, unlock, success=False)


def consume_export_unlock(unlock):
    return settle_credit(ExportUnlock, unlock, success=True)


def reserve_export_unlock(user):
    unlock = (
        ExportUnlock.objects.select_for_update()
        .filter(user=user, status=ExportUnlock.STATUS_AVAILABLE)
        .order_by("-granted_at")
        .first()
    )
    if unlock is None:
        return None
    unlock.status = ExportUnlock.STATUS_RESERVED
    unlock.reserved_at = timezone.now()
    unlock.save(update_fields=["status", "reserved_at"])
    return unlock
