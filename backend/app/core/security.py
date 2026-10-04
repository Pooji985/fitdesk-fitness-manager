import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User


_bearer_scheme = HTTPBearer(auto_error=False)
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1


def _jwt_secret() -> str:
    secret = settings.JWT_SECRET_KEY
    if not secret or len(secret) < 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured. Set JWT_SECRET_KEY to a random value of at least 32 characters.",
        )
    return secret


def _encode_segment(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode_segment(value: str) -> bytes:
    padded = value.encode("ascii") + b"=" * (-len(value) % 4)
    return base64.b64decode(padded, altchars=b"-_", validate=True)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=64,
    )
    return "$".join(
        (
            "scrypt",
            str(_SCRYPT_N),
            str(_SCRYPT_R),
            str(_SCRYPT_P),
            _encode_segment(salt),
            _encode_segment(digest),
        )
    )


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, n_value, r_value, p_value, salt_value, digest_value = password_hash.split("$")
        if algorithm != "scrypt":
            return False
        expected = _decode_segment(digest_value)
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=_decode_segment(salt_value),
            n=int(n_value),
            r=int(r_value),
            p=int(p_value),
            dklen=len(expected),
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, UnicodeError):
        return False


def create_access_token(user_id: int) -> str:
    secret = _jwt_secret()
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    header = _encode_segment(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _encode_segment(
        json.dumps(
            {"sub": str(user_id), "iat": int(issued_at.timestamp()), "exp": int(expires_at.timestamp())},
            separators=(",", ":"),
        ).encode()
    )
    signed_content = f"{header}.{payload}"
    signature = hmac.new(secret.encode("utf-8"), signed_content.encode("ascii"), hashlib.sha256).digest()
    return f"{signed_content}.{_encode_segment(signature)}"


def _decode_access_token(token: str) -> int:
    secret = _jwt_secret()
    header_segment, payload_segment, signature_segment = token.split(".")
    header = json.loads(_decode_segment(header_segment))
    if not isinstance(header, dict) or header.get("alg") != "HS256" or header.get("typ") != "JWT":
        raise ValueError("Unsupported token header")

    signed_content = f"{header_segment}.{payload_segment}"
    expected_signature = hmac.new(secret.encode("utf-8"), signed_content.encode("ascii"), hashlib.sha256).digest()
    if not hmac.compare_digest(_decode_segment(signature_segment), expected_signature):
        raise ValueError("Invalid token signature")

    payload = json.loads(_decode_segment(payload_segment))
    if not isinstance(payload, dict):
        raise ValueError("Invalid token payload")
    subject = payload.get("sub")
    expires_at = payload.get("exp")
    if not isinstance(subject, str) or not subject.isdecimal():
        raise ValueError("Invalid token subject")
    if not isinstance(expires_at, int) or expires_at <= int(datetime.now(timezone.utc).timestamp()):
        raise ValueError("Expired token")
    return int(subject)


def _resolve_current_user(token: str, db: Session) -> User:
    try:
        user_id = _decode_access_token(token)
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive account.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _resolve_current_user(credentials.credentials, db)


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if credentials is None:
        return None
    return _resolve_current_user(credentials.credentials, db)


def require_roles(*allowed_roles: str) -> Callable[..., User]:
    allowed = frozenset(allowed_roles)

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return current_user

    return role_checker