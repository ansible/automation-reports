import logging
import base64
import hashlib

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from django.conf import settings
from django.utils.encoding import smart_bytes, smart_str

logger = logging.getLogger("automation_dashboard.clusters.encryption")

class Fernet256(Fernet):
    """Not techincally Fernet, but uses the base of the Fernet spec and uses AES-256-CBC
    instead of AES-128-CBC. All other functionality remain identical.
    """

    def __init__(self, key: bytes | str):
        backend = default_backend()
        key = base64.urlsafe_b64decode(key)
        if len(key) != 64:
            raise ValueError("Fernet key must be 64 url-safe base64-encoded bytes.")

        self._signing_key = key[:32]
        self._encryption_key = key[32:]
        self._backend = backend


def get_encryption_key() -> bytes:
    logger.debug("Generating encryption key from SECRET_KEY.")
    h = hashlib.sha512()
    h.update(smart_bytes(settings.DATABASE_KEY))
    key = base64.urlsafe_b64encode(h.digest())
    logger.debug("Encryption key generated.")
    return key


def encrypt_value(value: str) -> bytes:
    logger.info("Encrypting value.")
    key = get_encryption_key()
    f = Fernet256(key)
    value = smart_str(value)
    encrypted = f.encrypt(smart_bytes(value))
    logger.debug("Value encrypted.")
    return encrypted


def decrypt_value(value: bytes) -> str:
    logger.info("Decrypting value.")
    key = get_encryption_key()
    f = Fernet256(key)
    if value == b'':
        logger.warning("Empty value detected for decryption.")
        decrypted = b''
    else:
        decrypted = f.decrypt(value)
        logger.debug("Value decrypted.")
    return smart_str(decrypted)
