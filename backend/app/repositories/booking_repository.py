from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models.booking import Booking
from app.models.room import Room
from app.models.room_slot import RoomSlot
from app.models.slot_template import SlotTemplate
from app.repositories.base import BaseRepository


# BookingRepository contains booking writes and taken-slot reads.
class BookingRepository(BaseRepository):
    def get_booking_by_id(self, booking_id: UUID) -> Booking | None:
        stmt = (
            select(Booking)
            .options(
                joinedload(Booking.room_slot).joinedload(RoomSlot.room),
                joinedload(Booking.room_slot).joinedload(RoomSlot.slot_template),
            )
            .where(Booking.id == booking_id)
        )
        return self.session.scalar(stmt)
    
    def list_taken_room_slots(self, *, room_id: UUID, booking_date: date) -> list[RoomSlot]:
        stmt = (
            select(RoomSlot)
            .join(RoomSlot.slot_template)
            .join(Booking, Booking.room_slot_id == RoomSlot.id)
            .options(
                joinedload(RoomSlot.room),
                joinedload(RoomSlot.slot_template),
            )
            .where(
                RoomSlot.room_id == room_id,
                Booking.booking_date == booking_date,
                Booking.cancelled_at.is_(None),
            )
            .order_by(SlotTemplate.start_time, SlotTemplate.end_time)
        )

        return list(self.session.scalars(stmt))

    def list_bookings_for_user(self, user_id: UUID, booking_date: date | None = None) -> list[Booking]:
        stmt = (
            select(Booking)
            .join(Booking.room_slot)
            .join(RoomSlot.room)
            .join(RoomSlot.slot_template)
            .options(
                joinedload(Booking.room_slot).joinedload(RoomSlot.room),
                joinedload(Booking.room_slot).joinedload(RoomSlot.slot_template),
            )
            .where(Booking.user_id == user_id)
            .order_by(
                Booking.booking_date.desc(),
                SlotTemplate.start_time.asc(),
                Room.number.asc(),
            )
        )

        if booking_date is not None:
            stmt = stmt.where(Booking.booking_date == booking_date)

        return list(self.session.scalars(stmt))

    # Leave constraint checks to the database and flush the new row right away.
    def create_booking(
        self,
        *,
        room_slot_id: UUID,
        booking_date: date,
        user_id: UUID,
        created_at: datetime,
    ) -> Booking:
        booking = Booking(
            room_slot_id=room_slot_id,
            booking_date=booking_date,
            user_id=user_id,
            created_at=created_at,
        )
        self.session.add(booking)
        self.session.flush()
        return booking

    # Repeated cancels stay harmless by keeping the first cancellation record.
    def cancel_booking(
        self,
        *,
        booking_id: UUID,
        cancelled_by_user_id: UUID,
        cancelled_at: datetime,
    ) -> Booking | None:
        booking = self.get_booking_by_id(booking_id)
        if booking is None:
            return None

        if booking.cancelled_at is None:
            booking.cancelled_by_user_id = cancelled_by_user_id
            booking.cancelled_at = cancelled_at
            self.session.flush()

        return booking
