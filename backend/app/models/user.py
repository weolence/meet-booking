from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.role import Role

class User(Base):
    """User model represents a user in the system with a unique login, password hash, and associated role."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("length(btrim(login)) > 0", name="users_login_not_blank"),
        CheckConstraint(
            "length(btrim(password_hash)) > 0",
            name="users_password_hash_not_blank",
        ),
    )

    # Login is the primary key for the User model and must be unique and non-empty.
    # Primary key may be changed to a UUID, but in terms of monolithic architecture, it is not necessary.
    login: Mapped[str] = mapped_column(String(128), primary_key=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
    )

    role: Mapped["Role"] = relationship(back_populates="users")
    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="user",
        foreign_keys="Booking.user_login",
    )
    cancelled_bookings: Mapped[list["Booking"]] = relationship(
        back_populates="cancelled_by_user",
        foreign_keys="Booking.cancelled_by_user_login",
    )
