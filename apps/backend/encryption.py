import os
import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken

def _get_fernet_key() -> bytes:
    """
    Returns a valid 32-byte url-safe base64-encoded Fernet key.
    Uses ENCRYPTION_KEY if valid, otherwise derives a deterministic key
    from JWT_SECRET so backend and worker containers always share the same key.
    """
    raw_key = os.getenv("ENCRYPTION_KEY")
    if raw_key:
        try:
            Fernet(raw_key.encode("utf-8"))
            return raw_key.encode("utf-8")
        except Exception:
            digest = hashlib.sha256(raw_key.encode("utf-8")).digest()
            return base64.urlsafe_b64encode(digest)

    secret_seed = os.getenv("JWT_SECRET", "super-secret-key-for-dev")
    digest = hashlib.sha256(f"jobpilot-fernet:{secret_seed}".encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)

fernet = Fernet(_get_fernet_key())

def encrypt_token(token: str) -> str:
    if not token:
        return None
    try:
        # Avoid double-encrypting if already a valid Fernet token
        fernet.decrypt(token.encode("utf-8"))
        return token
    except Exception:
        return fernet.encrypt(token.encode("utf-8")).decode("utf-8")

def decrypt_token(encrypted_token: str) -> str:
    if not encrypted_token:
        return None
    try:
        return fernet.decrypt(encrypted_token.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        # Graceful fallback for legacy plaintext tokens stored before encryption fix
        return encrypted_token
