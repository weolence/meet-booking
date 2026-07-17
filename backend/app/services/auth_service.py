from __future__ import annotations

from datetime import datetime, timedelta

from app.models.user import User
from app.repositories.revoked_token_repository import RevokedTokenRepository
from app.repositories.user_repository import UserRepository
from app.security.passwords import verify_password
from app.security.tokens import create_access_token, hash_access_token
from app.services.errors import InvalidCredentialsError


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        revoked_token_repository: RevokedTokenRepository,
        *,
        jwt_secret_key: str,
        jwt_algorithm: str,
        access_token_expire_minutes: int,
    ) -> None:
        self.user_repository = user_repository
        self.revoked_token_repository = revoked_token_repository
        self.jwt_secret_key = jwt_secret_key
        self.jwt_algorithm = jwt_algorithm
        self.access_token_expires_delta = timedelta(minutes=access_token_expire_minutes)

    def authenticate_user(self, *, login: str, password: str) -> User:
        normalized_login = login.strip()
        if not normalized_login:
            raise InvalidCredentialsError()

        user = self.user_repository.get_user_by_login(normalized_login)
        if user is None:
            raise InvalidCredentialsError()

        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()

        return user

    def create_access_token_for_user(self, *, user: User) -> str:
        return create_access_token(
            user_id=user.id,
            secret_key=self.jwt_secret_key,
            algorithm=self.jwt_algorithm,
            expires_delta=self.access_token_expires_delta,
        )

    def logout_user(
        self,
        *,
        user: User,
        access_token: str,
        expires_at: datetime,
    ) -> None:
        self.revoked_token_repository.revoke_token(
            token_hash=hash_access_token(access_token),
            user_id=user.id,
            expires_at=expires_at,
        )
