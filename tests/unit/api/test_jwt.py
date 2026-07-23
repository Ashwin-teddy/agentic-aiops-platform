import pytest
from app.core.security.jwt import create_access_token, create_refresh_token, verify_token, create_token_pair


class TestJWT:
    def test_create_and_verify_access_token(self) -> None:
        token = create_access_token(subject="user-123", roles=["admin"], permissions=["read:all"])
        payload = verify_token(token, expected_type="access")
        assert payload.sub == "user-123"
        assert "admin" in payload.roles

    def test_create_refresh_token(self) -> None:
        token = create_refresh_token(subject="user-123")
        payload = verify_token(token, expected_type="refresh")
        assert payload.sub == "user-123"

    def test_wrong_token_type_raises(self) -> None:
        token = create_refresh_token(subject="user-123")
        with pytest.raises(ValueError):
            verify_token(token, expected_type="access")

    def test_token_pair(self) -> None:
        pair = create_token_pair(subject="user-456", roles=["user"])
        assert pair.access_token
        assert pair.refresh_token
        assert pair.token_type == "bearer"

    def test_invalid_token_raises(self) -> None:
        with pytest.raises(ValueError):
            verify_token("invalid.token.here")
