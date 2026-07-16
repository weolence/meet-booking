from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin

if TYPE_CHECKING:
    from app.models.room_slot import RoomSlot
    from app.models.user import User


# Bookings point to room_slot to avoid duplicating room and slot columns.
class Booking(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "bookings"
    __table_args__ = (
        # A booking is either active, or it carries a full cancellation record.
        CheckConstraint(
            "("
            "cancelled_at IS NULL AND cancelled_by_user_id IS NULL"
            ") OR ("
            "cancelled_at IS NOT NULL AND cancelled_by_user_id IS NOT NULL"
            ")",
            name="bookings_cancellation_state",
        ),
        CheckConstraint(
            "cancelled_at IS NULL OR cancelled_at >= created_at",
            name="bookings_cancelled_at_after_created_at",
        ),
        # Only one active booking is allowed for the same room slot and date.
        Index(
            "uq_bookings_active_room_slot_date",
            "room_slot_id",
            "booking_date",
            unique=True,
            postgresql_where=text("cancelled_at IS NULL"),
        ),
        Index("ix_bookings_user_id_booking_date", "user_id", "booking_date"),
        Index(
            "ix_bookings_active_booking_date_room_slot_id",
            "booking_date",
            "room_slot_id",
            postgresql_where=text("cancelled_at IS NULL"),
        ),
    )

    room_slot_id: Mapped[UUID] = mapped_column(
        ForeignKey("room_slots.id", ondelete="RESTRICT"),
        nullable=False,
    )
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(nullable=True)
    cancelled_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )

    room_slot: Mapped["RoomSlot"] = relationship(back_populates="bookings")
    user: Mapped["User"] = relationship(
        back_populates="bookings",
        foreign_keys=[user_id],
    )
    cancelled_by_user: Mapped["User | None"] = relationship(
        back_populates="cancelled_bookings",
        foreign_keys=[cancelled_by_user_id],
    )
