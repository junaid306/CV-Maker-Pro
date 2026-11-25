from unittest.mock import patch

from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.advertisements.models import AdSession
from apps.rewards.services import record_verified_reward

from .models import AiFeatureSetting
from .services import FeatureDisabled, run_generation


class AiFlowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="f@x.com", password="ChangeMe123")
        self.feature = AiFeatureSetting.objects.create(feature="cover_letter", enabled=True)

    def _grant(self):
        session = AdSession.objects.create(user=self.user, purpose="ai", feature="cover_letter",
                                           required_count=1, status=AdSession.STATUS_OPEN)
        record_verified_reward(session, f"grant-{session.pk}")

    def test_feature_disabled_rejected(self):
        self.feature.enabled = False
        self.feature.save()
        with self.assertRaises(FeatureDisabled):
            run_generation(self.user, "cover_letter", input_text="text here")

    def test_generation_success_consumes_credit(self):
        self._grant()
        with patch("apps.ai_tools.services.generate_with_failover") as mock:
            mock.return_value = {"text": "Dear hiring manager...", "provider": "primary",
                                 "tokens_in": 10, "tokens_out": 20, "latency_ms": 25}
            generation = run_generation(self.user, "cover_letter", input_text="my background is software development")
            self.assertEqual(generation.status, "succeeded")
            self.assertEqual(generation.provider, "primary")
        from apps.rewards.models import AiGenerationCredit

        credit = AiGenerationCredit.objects.get(user=self.user)
        self.assertEqual(credit.status, "consumed")
