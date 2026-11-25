from unittest.mock import patch

from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.advertisements.models import AdSession
from apps.rewards.models import AiGenerationCredit
from apps.rewards.services import record_verified_reward

from .adapters import AdapterError, TransientError
from .manager import GenerationFailed, NoProviderAvailable, generate_with_failover
from .models import AiProvider

from apps.ai_tools.models import AiFeatureSetting
from apps.ai_tools.services import run_generation


class FailoverTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="ai@x.com", password="ChangeMe123")
        self.primary = AiProvider.objects.create(name="primary", adapter="openai", priority=1, max_retries=1)
        self.primary.set_api_key("k1")
        self.primary.save()
        self.backup = AiProvider.objects.create(name="backup", adapter="openai", priority=5, max_retries=1)
        self.backup.set_api_key("k2")
        self.backup.save()

    def _grant_credit(self, feature="grammar_correction"):
        session = AdSession.objects.create(user=self.user, purpose="ai", feature=feature, required_count=1,
                                           status=AdSession.STATUS_OPEN, verified_count=0)
        record_verified_reward(session, f"tx-{session.pk}")
        AiFeatureSetting.objects.create(feature=feature, enabled=True)

    def test_transient_failure_falls_over(self):
        self._grant_credit()
        with patch("apps.ai_providers.manager.get_adapter") as mock_get:
            adapter = mock_get.return_value
            adapter.generate.side_effect = [TransientError("429"), {"text": "fixed", "tokens_in": 5, "tokens_out": 2, "latency_ms": 10}]
            result = generate_with_failover("prompt")
            self.assertEqual(result["text"], "fixed")
            self.assertEqual(result["provider"], "backup")
            self.backup.refresh_from_db()
            self.assertTrue(self.backup.healthy)

    def test_credential_error_does_not_fail_over(self):
        self._grant_credit()
        with patch("apps.ai_providers.manager.get_adapter") as mock_get:
            mock_get.return_value.generate.side_effect = AdapterError("invalid credentials")
            with self.assertRaises(GenerationFailed):
                generate_with_failover("prompt")
            self.assertEqual(mock_get.call_count, 1)

    def test_no_credit_blocks_generation_and_no_provider_call(self):
        AiFeatureSetting.objects.create(feature="grammar_correction", enabled=True)
        with self.assertRaises(Exception):
            run_generation(self.user, "grammar_correction", input_text="hello there friend")
        self.assertFalse(AiGenerationCredit.objects.filter(user=self.user).exists())

    def test_reserved_credit_released_on_failure(self):
        self._grant_credit()
        with patch("apps.ai_providers.manager.get_adapter") as mock_get:
            mock_get.return_value.generate.side_effect = TransientError("503")
            with self.assertRaises(Exception):
                run_generation(self.user, "grammar_correction", input_text="hello there friend")
        credit = AiGenerationCredit.objects.get(user=self.user)
        self.assertEqual(credit.status, "available")

    def test_no_provider_available(self):
        AiProvider.objects.all().delete()
        with self.assertRaises(NoProviderAvailable):
            generate_with_failover("prompt")
