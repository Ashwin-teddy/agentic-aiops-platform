import bcrypt
import pytest


class TestPasswordHashing:
    def test_bcrypt_hash_and_verify(self):
        password = "test_password_123"
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        assert bcrypt.checkpw(password.encode(), hashed.encode())
        assert not bcrypt.checkpw(b"wrong_password", hashed.encode())

    def test_bcrypt_hash_is_not_plaintext(self):
        password = "my_secret"
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        assert hashed != password
        assert hashed.startswith("$2")

    def test_different_hashes_for_same_password(self):
        password = "same_password"
        h1 = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        h2 = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        assert h1 != h2
        assert bcrypt.checkpw(password.encode(), h1.encode())
        assert bcrypt.checkpw(password.encode(), h2.encode())
