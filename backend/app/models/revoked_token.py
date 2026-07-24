from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import IdMixin

class RevokedToken(IdMixin, Base):
    """RevokedToken model represents a JWT token that has been revoked and is no longer valid for authentication."""

    __tablename__ = "revoked_tokens"
    __table_args__ = (
        Index("uq_revoked_tokens_token_hash", "token_hash", unique=True),
        Index("ix_revoked_tokens_expires_at", "expires_at"),
        Index("ix_revoked_tokens_user_login", "user_login"),
    )

    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    user_login: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("users.login", ondelete="CASCADE"),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
