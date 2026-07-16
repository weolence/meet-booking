from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import IdMixin

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.role import Role


# Users keep a foreign key to roles instead of a free-form role string.
class User(IdMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("length(btrim(login)) > 0", name="users_login_not_blank"),
        CheckConstraint(
            "length(btrim(password_hash)) > 0",
            name="users_password_hash_not_blank",
        ),
        Index("uq_users_login", "login", unique=True),
        Index("ix_users_role_id", "role_id"),
    )

    login: Mapped[str] = mapped_column(String(128), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
    )

    role: Mapped["Role"] = relationship(back_populates="users")
    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="user",
        foreign_keys="Booking.user_id",
    )
    cancelled_bookings: Mapped[list["Booking"]] = relationship(
        back_populates="cancelled_by_user",
        foreign_keys="Booking.cancelled_by_user_id",
    )
