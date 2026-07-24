from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.room_slot import RoomSlot
    from app.models.user import User

class Booking(Base):
    """Booking model represents a booking made by a user for a specific room slot on a specific date."""

    __tablename__ = "bookings"
    __table_args__ = (
        # Only one active booking is allowed for the same room slot and date.
        Index(
            "uq_bookings_active_room_slot_date",
            "room_slot_id",
            "booking_date",
            unique=True,
            postgresql_where=text("cancelled_by_user_login IS NULL"),
        ),
        Index("ix_bookings_user_login_booking_date", "user_login", "booking_date"),
        Index(
            "ix_bookings_active_booking_date_room_slot_id",
            "booking_date",
            "room_slot_id",
            postgresql_where=text("cancelled_by_user_login IS NULL"),
        ),
    )

    # Primary key is a composite key consisting of user_login, room_slot_id, and booking_date.
    user_login: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("users.login", ondelete="RESTRICT"),
        primary_key=True,
    )
    room_slot_id: Mapped[int] = mapped_column(
        ForeignKey("room_slots.id", ondelete="RESTRICT"),
        primary_key=True,
        nullable=False,
    )
    booking_date: Mapped[date] = mapped_column(
        Date,
        primary_key=True,
        nullable=False,
    )
    # The login of the user who cancelled the booking, if applicable. This field is nullable.
    cancelled_by_user_login: Mapped[str | None] = mapped_column(
        String(128),
        ForeignKey("users.login", ondelete="RESTRICT"),
        nullable=True,
    )

    room_slot: Mapped["RoomSlot"] = relationship(back_populates="bookings")
    user: Mapped["User"] = relationship(
        back_populates="bookings",
        foreign_keys=[user_login],
    )
    cancelled_by_user: Mapped["User | None"] = relationship(
        back_populates="cancelled_bookings",
        foreign_keys=[cancelled_by_user_login],
    )
