import pytest
from backend.apps.clusters import encryption


class TestEncryption:

    def test_encrypt_and_decrypt_value(self):
        original = "my_secret_value"
        encrypted = encryption.encrypt_value(original)
        assert isinstance(encrypted, bytes)
        decrypted = encryption.decrypt_value(encrypted)
        assert decrypted == original

    def test_encrypt_value_different_outputs(self):
        value1 = "value1"
        value2 = "value2"
        encrypted1 = encryption.encrypt_value(value1)
        encrypted2 = encryption.encrypt_value(value2)
        assert encrypted1 != encrypted2

    def test_encrypt_unique_outputs(self):
        value = "value_test"
        encrypted1 = encryption.encrypt_value(value)
        encrypted2 = encryption.encrypt_value(value)
        assert encrypted1 != encrypted2

    def test_decrypt_invalid_value_raises(self):
        with pytest.raises(Exception):
            encryption.decrypt_value(b"not_a_valid_encrypted_value")
