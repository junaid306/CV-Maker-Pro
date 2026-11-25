from unittest.mock import patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.advertisements.models import AdSession, AdSetting
from apps.advertisements.verification import build_message_from_query, verify_ssv_query

from apps.rewards.services import open_reward_session


def make_ssv_payload(private_key, params):
    from urllib.parse import urlencode

    query = urlencode(params)
    signature = private_key.sign(build_message_from_query(query))
    import base64

    encoded = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    return query, encoded


class SsvTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="s@x.com", password="ChangeMe123")
        self.private_key = Ed25519PrivateKey.generate()
        self.public_pem = self.private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

    def test_valid_signature_is_recorded(self):
        session = open_reward_session(self.user, "ai", "cover_letter")
        query, signature = make_ssv_payload(self.private_key, {
            "transaction_id": "ssv-tx-1", "user_id": self.user.pk, "timestamp": "1700000000",
        })
        ok = verify_ssv_query(query, signature, pem_override=self.public_pem)
        self.assertTrue(ok)

    def test_tampered_query_fails(self):
        query, signature = make_ssv_payload(self.private_key, {"transaction_id": "ssv-tx-2", "user_id": 1})
        tampered = query + "&transaction_id=CHANGED"
        ok = verify_ssv_query(tampered, signature, pem_override=self.public_pem)
        self.assertFalse(ok)

    def test_ssv_endpoint_get_records_reward(self):
        session = open_reward_session(self.user, "ai", "cover_letter")
        query, signature = make_ssv_payload(self.private_key, {
            "transaction_id": "ssv-tx-3", "user_id": self.user.pk,
        })
        with patch("apps.advertisements.verification.load_public_key", return_value=self.private_key.public_key()):
            response = self.client.get(f"/api/v1/ads/ssv/?{query}&signature={signature}&key_id=1")
        self.assertEqual(response.status_code, 200)
        session.refresh_from_db()
        self.assertEqual(session.verified_count, 1)

    def test_ssv_endpoint_rejects_bad_signature(self):
        session = open_reward_session(self.user, "ai", "cover_letter")
        with patch("apps.advertisements.verification.load_public_key", return_value=self.private_key.public_key()):
            response = self.client.get("/api/v1/ads/ssv/?transaction_id=abc&signature=AAAA&key_id=1")
        self.assertEqual(response.status_code, 400)
        session.refresh_from_db()
        self.assertEqual(session.verified_count, 0)

    def test_endpoint_requires_knowledge_without_signature(self):
        session = open_reward_session(self.user, "ai", "cover_letter")
        with patch("apps.advertisements.verification.load_public_key", return_value=None):
            response = self.client.get("/api/v1/ads/ssv/?transaction_id=x1")
        self.assertEqual(response.status_code, 400)
        session.refresh_from_db()
        self.assertEqual(session.verified_count, 0)
