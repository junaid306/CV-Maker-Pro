from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.advertisements.models import AdReward, AdSession
from apps.rewards.models import AiGenerationCredit, ExportUnlock
from apps.rewards.services import record_verified_reward, reserve_ai_credit, reserve_export_unlock, settle_credit


class RewardFlowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="r@x.com", password="ChangeMe123")

    def _session(self, purpose="ai"):
        return AdSession.objects.create(
            user=self.user, purpose=purpose, required_count=2, feature="grammar_correction" if purpose == "ai" else ""
        )

    def test_credit_granted_after_required_verified_ads(self):
        session = self._session()
        _, granted = record_verified_reward(session, "tx-1")
        self.assertFalse(granted)
        session.refresh_from_db()
        self.assertEqual(session.verified_count, 1)
        _, granted = record_verified_reward(session, "tx-2")
        self.assertTrue(granted)
        self.assertTrue(AiGenerationCredit.objects.filter(user=self.user, status="available").exists())

    def test_duplicate_transaction_rejected(self):
        session = self._session()
        record_verified_reward(session, "dup-tx")
        record_verified_reward(session, "dup-tx")
        self.assertEqual(AdReward.objects.filter(transaction_id="dup-tx").count(), 1)
        self.assertEqual(self.user.ad_rewards.filter(transaction_id="dup-tx").count(), 1)

    def test_export_rewards_independent(self):
        session = self._session(purpose="export")
        for index in range(2):
            record_verified_reward(session, f"ex-{index}")
        self.assertTrue(ExportUnlock.objects.filter(user=self.user, status="available").exists())
        # AI credits remain untouched
        self.assertFalse(AiGenerationCredit.objects.filter(user=self.user).exists())

    def test_credit_reserve_consume_release(self):
        session = self._session()
        record_verified_reward(session, "tx-1")
        record_verified_reward(session, "tx-2")
        credit = reserve_ai_credit(self.user, "grammar_correction")
        self.assertEqual(credit.status, "reserved")
        self.assertEqual(reserve_ai_credit(self.user, "grammar_correction"), None)
        settle_credit(AiGenerationCredit, credit, success=False)
        credit.refresh_from_db()
        self.assertEqual(credit.status, "available")
        credit = reserve_ai_credit(self.user, "grammar_correction")
        settle_credit(AiGenerationCredit, credit, success=True)
        self.assertEqual(reserve_ai_credit(self.user, "grammar_correction"), None)

    def test_export_unlock_reserve_and_release(self):
        session = self._session(purpose="export")
        record_verified_reward(session, "ex-a")
        record_verified_reward(session, "ex-b")
        unlock = reserve_export_unlock(self.user)
        self.assertEqual(unlock.status, "reserved")
        release = ExportUnlock.objects.get(pk=unlock.pk)
        from apps.rewards.services import release_export_unlock

        release_export_unlock(unlock)
        unlock.refresh_from_db()
        self.assertEqual(unlock.status, "available")
