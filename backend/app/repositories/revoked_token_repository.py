from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from app.models.revoked_token import RevokedToken
from app.repositories.base import BaseRepository

class RevokedTokenRepository(BaseRepository):
    """Repository for managing revoked tokens in the database."""

    def get_revoked_token_by_hash(self, token_hash: str) -> RevokedToken | None:
        """Retrieves a revoked token by its hash. Returns None if not found."""

        stmt = select(RevokedToken).where(RevokedToken.token_hash == token_hash)
        return self.session.scalar(stmt)

    def is_token_revoked(self, token_hash: str) -> bool:
        """Checks if a token is revoked by its hash. Returns True if revoked, False otherwise."""

        return self.get_revoked_token_by_hash(token_hash) is not None

    def revoke_token(
        self,
        *,
        token_hash: str,
        user_login: str,
        expires_at: datetime,
    ) -> RevokedToken:
        """Revokes a token by its hash. If the token is already revoked, it will be returned instead."""

        revoked_token = self.get_revoked_token_by_hash(token_hash)
        if revoked_token is not None:
            return revoked_token

        revoked_token = RevokedToken(
            token_hash=token_hash,
            user_login=user_login,
            expires_at=expires_at,
        )
        self.session.add(revoked_token)
        self.session.flush()
        return revoked_token

    def remove_expired_tokens(self, *, now: datetime | None = None) -> int:
        """Removes all expired revoked tokens from the database. Returns the number of tokens removed."""

        cutoff = now or datetime.now(timezone.utc)
        expired_tokens = list(
            self.session.scalars(
                select(RevokedToken).where(RevokedToken.expires_at <= cutoff)
            )
        )
        for revoked_token in expired_tokens:
            self.session.delete(revoked_token)

        self.session.flush()
        return len(expired_tokens)
