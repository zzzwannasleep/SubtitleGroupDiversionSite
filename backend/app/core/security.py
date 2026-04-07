import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings


PASSWORD_HASH_PREFIX = "bcrypt_sha256$v1$"


def _password_digest(password: str) -> bytes:
    return hashlib.sha256(password.encode("utf-8")).hexdigest().encode("ascii")


def hash_password(password: str) -> str:
    # Pre-hash before bcrypt so bcrypt never receives input above its 72-byte cap.
    hashed_password = bcrypt.hashpw(_password_digest(password), bcrypt.gensalt())
    return f"{PASSWORD_HASH_PREFIX}{hashed_password.decode('ascii')}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password.startswith(PASSWORD_HASH_PREFIX):
        return False

    try:
        bcrypt_hash = hashed_password.removeprefix(PASSWORD_HASH_PREFIX).encode("ascii")
        return bcrypt.checkpw(_password_digest(plain_password), bcrypt_hash)
    except ValueError:
        return False


def create_access_token(subject: str) -> str:
    settings = get_settings()
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": subject, "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")


def decode_access_token(token: str) -> str | None:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
    except JWTError:
        return None
    subject = payload.get("sub")
    if not isinstance(subject, str):
        return None
    return subject


def generate_tracker_credential() -> str:
    # XBT's torrent_pass schema expects a 32-character private credential.
    return secrets.token_hex(16)


def generate_rss_key() -> str:
    return secrets.token_hex(24)


def mask_secret(value: str) -> str:
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"
