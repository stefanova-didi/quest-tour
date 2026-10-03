import hashlib
import secrets


def generate_token() -> str:
    """256 bits of randomness, URL-safe (R-21 requires >= 128)."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
