from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.dependencies.repositories import get_revoked_token_repository, get_user_repository
from app.config.roles import ADMIN_ROLE_NAME
from app.config.settings import Settings, get_settings
from app.models.user import User
from app.repositories.revoked_token_repository import RevokedTokenRepository
from app.repositories.user_repository import UserRepository
from app.security.tokens import (
    AccessTokenPayload,
    InvalidAccessTokenError,
    decode_access_token,
    hash_access_token,
)


bearer_scheme = HTTPBearer(auto_error=False, scheme_name="BearerAuth")


def get_bearer_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return credentials.credentials


def get_current_access_token_payload(
    token: Annotated[str, Depends(get_bearer_token)],
    revoked_token_repository: Annotated[
        RevokedTokenRepository,
        Depends(get_revoked_token_repository),
    ],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AccessTokenPayload:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token_payload = decode_access_token(
            token=token,
            secret_key=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
    except InvalidAccessTokenError as exc:
        raise credentials_exception from exc

    if revoked_token_repository.is_token_revoked(hash_access_token(token)):
        raise credentials_exception

    return token_payload


def get_current_user(
    token_payload: Annotated[AccessTokenPayload, Depends(get_current_access_token_payload)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user = user_repository.get_user_by_login(token_payload.user_login)
    if user is None:
        raise credentials_exception

    return user


def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.role.role != ADMIN_ROLE_NAME:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role is required.",
        )

    return current_user
