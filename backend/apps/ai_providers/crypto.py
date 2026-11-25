"""Encryption for AI provider API keys at rest (Fernet, key from env)."""
import base64

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from django.conf import settings


def _fernet():
    raw = settings.FIELD_ENCRYPTION_KEY
    if raw:
        try:
            key = base64.urlsafe_b64decode(raw)
        except Exception:
            key = b""
        if len(key) != 32:
            digest = hashes.Hash(hashes.SHA256())
            digest.update(raw.encode())
            key = digest.finalize()
        return Fernet(base64.urlsafe_b64encode(key))
    raise RuntimeError("FIELD_ENCRYPTION_KEY is not configured; refusing to store API keys.")


def encrypt_secret(plain_value):
    if not plain_value:
        return ""
    f = _fernet()
    return f.encrypt(plain_value.encode()).decode()


def decrypt_secret(encrypted_value):
    if not encrypted_value:
        return ""
    try:
        f = _fernet()
        return f.decrypt(encrypted_value.encode()).decode()
    except InvalidToken as err:
        raise ValueError("Stored API key cannot be decrypted; replace the key in admin.") from err
