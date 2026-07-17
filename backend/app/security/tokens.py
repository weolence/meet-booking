from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from uuid import UUID

import jwt
from jwt import InvalidTokenError

from app.security.errors import InvalidAccessTokenError


ACCESS_TOKEN_TYPE = "access"


@dataclass(frozen=True, slots=True)
class AccessTokenPayload:
    user_id: UUID
    expires_at: datetime


def create_access_token(
    *,
    user_id: UUID,
    secret_key: str,
    algorithm: str,
    expires_delta: timedelta,
    now: datetime | None = None,
) -> str:
    issued_at = now or datetime.now(timezone.utc)
    expires_at = issued_at + expires_delta
    payload = {
        "sub": str(user_id),
        "type": ACCESS_TOKEN_TYPE,
        "iat": issued_at,
        "exp": expires_at,
    }
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def hash_access_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def decode_access_token(
    *,
    token: str,
    secret_key: str,
    algorithm: str,
) -> AccessTokenPayload:
    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[algorithm],
            options={"require": ["sub", "type", "exp"]},
        )
    except InvalidTokenError as exc:
        raise InvalidAccessTokenError() from exc

    subject = payload.get("sub")
    token_type = payload.get("type")
    expires_at = payload.get("exp")

    if not isinstance(subject, str) or token_type != ACCESS_TOKEN_TYPE:
        raise InvalidAccessTokenError()

    if not isinstance(expires_at, int):
        raise InvalidAccessTokenError()

    try:
        user_id = UUID(subject)
    except ValueError as exc:
        raise InvalidAccessTokenError() from exc

    return AccessTokenPayload(
        user_id=user_id,
        expires_at=datetime.fromtimestamp(expires_at, tz=timezone.utc),
    )
