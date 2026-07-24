from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.dependencies import (
    get_auth_service,
    get_current_access_token_payload,
    get_current_user,
    oauth2_scheme,
)
from app.models.user import User
from app.api.errors import service_error_to_http
from app.api.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.api.schemas.users import UserResponse
from app.security.tokens import AccessTokenPayload
from app.services.auth_service import AuthService
from app.services.errors import InvalidCredentialsError, ServiceError


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    try:
        user = auth_service.register_user(
            login=request.login,
            password=request.password,
        )
    except ServiceError as exc:
        raise service_error_to_http(exc) from exc

    return UserResponse.from_user(user)


@router.post("/login", response_model=TokenResponse)
def login(
    request: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    try:
        user = auth_service.authenticate_user(
            login=request.login,
            password=request.password,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login or password.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return TokenResponse(access_token=auth_service.create_access_token_for_user(user=user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    token: Annotated[str, Depends(oauth2_scheme)],
    token_payload: Annotated[
        AccessTokenPayload,
        Depends(get_current_access_token_payload),
    ],
    current_user: Annotated[User, Depends(get_current_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> Response:
    auth_service.logout_user(
        user=current_user,
        access_token=token,
        expires_at=token_payload.expires_at,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
