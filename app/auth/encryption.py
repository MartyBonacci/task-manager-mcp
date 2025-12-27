"""
Token encryption utilities using Fernet (AES-256).

This module provides functions to encrypt and decrypt OAuth tokens
at rest in the database using AES-256 encryption via Fernet.
"""

from cryptography.fernet import Fernet

from app.config.settings import settings


def get_cipher() -> Fernet:
    """
    Get Fernet cipher instance using ENCRYPTION_KEY from settings.

    Returns:
        Fernet: Cipher instance for encryption/decryption.

    Raises:
        ValueError: If ENCRYPTION_KEY is not set or invalid.
    """
    if not settings.ENCRYPTION_KEY:
        raise ValueError("ENCRYPTION_KEY not configured in settings")

    # Ensure key is bytes
    encryption_key = settings.ENCRYPTION_KEY.encode() if isinstance(settings.ENCRYPTION_KEY, str) else settings.ENCRYPTION_KEY

    return Fernet(encryption_key)


def encrypt_token(token: str) -> bytes:
    """
    Encrypt a token string using Fernet (AES-256).

    Args:
        token: The token string to encrypt.

    Returns:
        bytes: Encrypted token as bytes.

    Raises:
        ValueError: If token is empty.
    """
    if not token:
        raise ValueError("Cannot encrypt empty token")

    cipher = get_cipher()
    token_bytes = token.encode()
    encrypted = cipher.encrypt(token_bytes)

    return encrypted


def decrypt_token(encrypted_token: bytes) -> str:
    """
    Decrypt an encrypted token back to string.

    Args:
        encrypted_token: The encrypted token bytes.

    Returns:
        str: Decrypted token string.

    Raises:
        ValueError: If encrypted_token is empty.
        cryptography.fernet.InvalidToken: If decryption fails.
    """
    if not encrypted_token:
        raise ValueError("Cannot decrypt empty token")

    cipher = get_cipher()
    decrypted_bytes = cipher.decrypt(encrypted_token)
    token = decrypted_bytes.decode()

    return token
