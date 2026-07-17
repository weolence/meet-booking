from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config.settings import Settings, get_settings
from app.db.session import get_db_session
from app.models.user import User
from app.repositories.revoked_token_repository import RevokedTokenRepository
from app.repositories.user_repository import UserRepository
from app.security.tokens import (
    AccessTokenPayload,
    InvalidAccessTokenError,
    decode_access_token,
    hash_access_token,
)
from app.services.auth_service import AuthService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_user_repository(
    session: Annotated[Session, Depends(get_db_session)],
) -> UserRepository:
    return UserRepository(session)


def get_revoked_token_repository(
    session: Annotated[Session, Depends(get_db_session)],
) -> RevokedTokenRepository:
    return RevokedTokenRepository(session)


def get_auth_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    revoked_token_repository: Annotated[
        RevokedTokenRepository,
        Depends(get_revoked_token_repository),
    ],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    return AuthService(
        user_repository,
        revoked_token_repository,
        jwt_secret_key=settings.jwt_secret_key,
        jwt_algorithm=settings.jwt_algorithm,
        access_token_expire_minutes=settings.jwt_access_token_expire_minutes,
    )


def get_current_access_token_payload(
    token: Annotated[str, Depends(oauth2_scheme)],
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

    user = user_repository.get_user_by_id(token_payload.user_id)
    if user is None:
        raise credentials_exception

    return user
