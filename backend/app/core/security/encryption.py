from __future__ import annotations

import base64
import hashlib
import re
import secrets

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config.settings import settings

_PII_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "phone": re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
    "ip_address": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "aws_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "jwt_token": re.compile(r"eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+"),
}


def _derive_key(passphrase: str | None = None) -> bytes:
    key_source = passphrase or settings.encryption_key
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"agentic-aiops-salt",
        iterations=480000,
    )
    return base64.urlsafe_b64encode(kdf.derive(key_source.encode()))


_fernet = Fernet(_derive_key())


def encrypt_value(value: str) -> str:
    return _fernet.encrypt(value.encode()).decode()


def decrypt_value(encrypted_value: str) -> str:
    return _fernet.decrypt(encrypted_value.encode()).decode()


def mask_pii(text: str) -> str:
    masked = text
    for pii_type, pattern in _PII_PATTERNS.items():
        if pii_type == "email":
            masked = pattern.sub(lambda m: m.group()[0] + "***@" + m.group().split("@")[1], masked)
        elif pii_type == "aws_key":
            masked = pattern.sub("AKIA***" + "***" * 3, masked)
        elif pii_type == "jwt_token":
            masked = pattern.sub("[REDACTED_JWT]", masked)
        else:
            masked = pattern.sub("[REDACTED]", masked)
    return masked


def generate_api_key() -> str:
    return secrets.token_urlsafe(32)


def hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()
