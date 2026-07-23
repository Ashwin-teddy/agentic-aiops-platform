import pytest
from app.core.security.encryption import encrypt_value, decrypt_value, mask_pii, generate_api_key


class TestEncryption:
    def test_encrypt_decrypt_roundtrip(self) -> None:
        original = "super-secret-password-123"
        encrypted = encrypt_value(original)
        decrypted = decrypt_value(encrypted)
        assert decrypted == original
        assert encrypted != original

    def test_mask_pii_email(self) -> None:
        masked = mask_pii("Contact john.doe@company.com for help")
        assert "john.doe@company.com" not in masked
        assert "@company.com" in masked

    def test_mask_pii_ip(self) -> None:
        masked = mask_pii("Server at 192.168.1.100 is down")
        assert "192.168.1.100" not in masked

    def test_mask_pii_aws_key(self) -> None:
        masked = mask_pii("Key: AKIAIOSFODNN7EXAMPLE")
        assert "AKIAIOSFODNN7EXAMPLE" not in masked

    def test_generate_api_key_length(self) -> None:
        key = generate_api_key()
        assert len(key) > 20
