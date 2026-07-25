from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models.booking import Booking
from app.models.room import Room
from app.models.room_slot import RoomSlot
from app.models.slot_template import SlotTemplate
from app.repositories.base import BaseRepository

class BookingRepository(BaseRepository):
    """BookingRepository contains booking writes and taken-slot reads."""

    def get_booking(
        self,
        *,
        user_login: str,
        room_slot_id: int,
        booking_date: date,
    ) -> Booking | None:
        """Gets a booking by composite primary key (user_login, room_slot_id, booking_date). Returns None if not found."""

        stmt = (
            select(Booking)
            .options(
                joinedload(Booking.room_slot).joinedload(RoomSlot.room),
                joinedload(Booking.room_slot).joinedload(RoomSlot.slot_template),
            )
            .where(
                Booking.user_login == user_login,
                Booking.room_slot_id == room_slot_id,
                Booking.booking_date == booking_date,
            )
        )
        return self.session.scalar(stmt)

    def get_active_booking_for_room_slot(
        self,
        *,
        room_slot_id: int,
        booking_date: date,
    ) -> Booking | None:
        """Gets the active booking for a room slot and date, regardless of owner."""

        stmt = (
            select(Booking)
            .options(
                joinedload(Booking.room_slot).joinedload(RoomSlot.room),
                joinedload(Booking.room_slot).joinedload(RoomSlot.slot_template),
            )
            .where(
                Booking.room_slot_id == room_slot_id,
                Booking.booking_date == booking_date,
                Booking.cancelled_by_user_login.is_(None),
            )
        )
        return self.session.scalar(stmt)

    def list_active_bookings_for_date(self, *, room_id: int, booking_date: date) -> list[RoomSlot]:
        """Lists all active bookings for a given date and room."""

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
                Booking.cancelled_by_user_login.is_(None),
            )
            .order_by(SlotTemplate.start_time, SlotTemplate.end_time)
        )

        return list(self.session.scalars(stmt))

    def list_bookings_for_user(self, user_login: str, booking_date: date | None = None) -> list[Booking]:
        """Lists all bookings for a user, optionally filtered by booking date. Returns an empty list if no bookings are found."""

        stmt = (
            select(Booking)
            .join(Booking.room_slot)
            .join(RoomSlot.room)
            .join(RoomSlot.slot_template)
            .options(
                joinedload(Booking.room_slot).joinedload(RoomSlot.room),
                joinedload(Booking.room_slot).joinedload(RoomSlot.slot_template),
            )
            .where(Booking.user_login == user_login)
            .order_by(
                Booking.booking_date.desc(),
                SlotTemplate.start_time.asc(),
                Room.name.asc(),
            )
        )

        if booking_date is not None:
            stmt = stmt.where(Booking.booking_date == booking_date)

        return list(self.session.scalars(stmt))

    def create_booking(
        self,
        *,
        room_slot_id: int,
        booking_date: date,
        user_login: str,
    ) -> Booking:
        """Creates a new booking for a user, room slot, and date. If a booking already exists for the same composite key, it will be returned instead.
        If the existing booking was cancelled, it will be reactivated. Returns the created or existing booking.
        Leave constraint checks to the database and flush the new row right away.
        """

        existing_booking = self.get_booking(
            user_login=user_login,
            room_slot_id=room_slot_id,
            booking_date=booking_date,
        )
        if existing_booking is not None:
            if existing_booking.cancelled_by_user_login is not None:
                existing_booking.cancelled_by_user_login = None
                self.session.flush()

            return existing_booking

        booking = Booking(
            room_slot_id=room_slot_id,
            booking_date=booking_date,
            user_login=user_login,
        )
        self.session.add(booking)
        self.session.flush()
        return booking

    def cancel_booking(
        self,
        *,
        user_login: str,
        room_slot_id: int,
        booking_date: date,
        cancelled_by_user_login: str,
    ) -> Booking | None:
        """Cancels a booking for a user, room slot, and date. If the booking does not exist, returns None.
        If the booking is already cancelled, it will remain unchanged.
        Repeated cancels stay harmless by keeping the first cancellation record.
        """

        booking = self.get_booking(
            user_login=user_login,
            room_slot_id=room_slot_id,
            booking_date=booking_date,
        )
        if booking is None:
            return None

        if booking.cancelled_by_user_login is None:
            booking.cancelled_by_user_login = cancelled_by_user_login
            self.session.flush()

        return booking
