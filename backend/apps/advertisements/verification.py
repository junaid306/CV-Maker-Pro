"""AdMob Server-Side Verification (SSV) support.

AdMob rewarded-ad SSV callbacks carry a signed query string. The signature is
an Ed25519 signature over the full query string excluding the `signature` and
`key_id` parameters, produced by the key published at
https://www.gstatic.com/admob/reward/keys/ . This module verifies such
callbacks strictly server-side; client assertions are never trusted.
"""
import base64
import json
import logging

import requests
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from django.conf import settings as dj_settings

from .models import AdSetting

logger = logging.getLogger(__name__)

KEYS_URL = "https://www.gstatic.com/admob/reward/keys/"


def load_public_key(key_id=None, pem_override=None):
    if pem_override is None:
        setting = AdSetting.load()
        if setting.ssv_public_key_pem and (key_id is None or key_id in (setting.ssv_key_id, None)):
            pem_override = setting.ssv_public_key_pem
    if pem_override:
        from cryptography.hazmat.primitives import serialization

        return serialization.load_pem_public_key(pem_override.encode())
    key_id = key_id or dj_settings.ADMOB_SSV_PUBLIC_KEY_ID
    pinned = dj_settings.ADMOB_SSV_PUBLIC_KEY
    if pinned and key_id:
        from cryptography.hazmat.primitives import serialization

        return serialization.load_pem_public_key(pinned.encode())
    keys = fetch_google_public_keys()
    if key_id:
        for entry in keys:
            if str(entry.get("keyId")) == str(key_id):
                from cryptography.hazmat.primitives import serialization

                return serialization.load_pem_public_key(entry["pem"].encode())
    return None


def fetch_google_public_keys():
    try:
        response = requests.get(KEYS_URL, timeout=5)
        response.raise_for_status()
        return json.loads(response.text).get("keys", [])
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not fetch AdMob SSV public keys: %s", exc)
        return []


def build_message_from_query(query_string):
    """Reconstruct the message signed by AdMob from a raw callback query string."""
    parts = []
    for chunk in query_string.split("&"):
        key = chunk.split("=", 1)[0]
        if key in ("signature", "key_id"):
            continue
        parts.append(chunk)
    return "&".join(parts).encode()


def verify_ssv_query(query_string, signature_b64, key_id=None, pem_override=None):
    """Verify an AdMob SSV callback query string. Returns True only on valid signature."""
    public_key = load_public_key(key_id, pem_override)
    if public_key is None:
        logger.warning("No AdMob SSV public key available for key_id=%s", key_id)
        return False
    message = build_message_from_query(query_string)
    try:
        signature = base64.urlsafe_b64decode(signature_b64 + "=" * (-len(signature_b64) % 4))
        public_key.verify(signature, message)
        return True
    except (InvalidSignature, ValueError) as exc:
        logger.info("AdMob SSV signature verification failed: %s", exc)
        return False
