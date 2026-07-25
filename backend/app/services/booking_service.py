from __future__ import annotations

from datetime import date

from sqlalchemy.exc import IntegrityError

from app.config.roles import ADMIN_ROLE_NAME
from app.models.booking import Booking
from app.models.user import User
from app.repositories.booking_repository import BookingRepository
from app.repositories.room_repository import RoomRepository
from app.repositories.user_repository import UserRepository
from app.services.errors import (
    ActiveBookingNotFoundError,
    BookingConflictError,
    BookingNotFoundError,
    BookingPermissionDeniedError,
    RoomSlotNotFoundError,
    UserNotFoundError,
)

class BookingService:
    """Service for handling booking creation and cancellation logic."""

    def __init__(
        self,
        booking_repository: BookingRepository,
        room_repository: RoomRepository,
        user_repository: UserRepository,
    ) -> None:
        self.booking_repository = booking_repository
        self.room_repository = room_repository
        self.user_repository = user_repository

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

        user = self.user_repository.get_user_by_login(user_login)
        if user is None:
            raise UserNotFoundError(user_login)

        room_slot = self.room_repository.get_room_slot_by_id(room_slot_id)
        if room_slot is None:
            raise RoomSlotNotFoundError(room_slot_id)

        taken_room_slot_ids = {
            taken_room_slot.id
            for taken_room_slot in self.booking_repository.list_active_bookings_for_date(
                room_id=room_slot.room_id,
                booking_date=booking_date,
            )
        }
        if room_slot_id in taken_room_slot_ids:
            raise BookingConflictError(room_slot_id=room_slot_id, booking_date=booking_date)

        try:
            with self.booking_repository.session.begin_nested():
                return self.booking_repository.create_booking(
                    room_slot_id=room_slot_id,
                    booking_date=booking_date,
                    user_login=user.login,
                )
        except IntegrityError as exc:
            raise BookingConflictError(room_slot_id=room_slot_id, booking_date=booking_date) from exc

    def cancel_active_booking_for_room_slot(
        self,
        *,
        room_slot_id: int,
        booking_date: date,
        cancelled_by_user_login: str,
    ) -> Booking:
        """Cancels the active booking for a room slot and date.

        Regular users can only cancel their own active booking. Admins can cancel
        whichever active booking occupies the slot.
        """

        booking = self.booking_repository.get_active_booking_for_room_slot(
            room_slot_id=room_slot_id,
            booking_date=booking_date,
        )
        if booking is None:
            raise ActiveBookingNotFoundError(
                room_slot_id=room_slot_id,
                booking_date=booking_date,
            )

        return self.cancel_booking(
            user_login=booking.user_login,
            room_slot_id=room_slot_id,
            booking_date=booking_date,
            cancelled_by_user_login=cancelled_by_user_login,
        )

    def cancel_booking(
        self,
        *,
        user_login: str,
        room_slot_id: int,
        booking_date: date,
        cancelled_by_user_login: str,
    ) -> Booking:
        """Cancels a booking for a user, room slot, and date. If the booking does not exist, raises BookingNotFoundError.
        If the booking is already cancelled, it will remain unchanged.
        Repeated cancels stay harmless by keeping the first cancellation record.
        """

        booking = self.booking_repository.get_booking(
            user_login=user_login,
            room_slot_id=room_slot_id,
            booking_date=booking_date,
        )
        if booking is None:
            raise BookingNotFoundError(
                user_login=user_login,
                room_slot_id=room_slot_id,
                booking_date=booking_date,
            )

        cancelled_by_user = self.user_repository.get_user_by_login(cancelled_by_user_login)
        if cancelled_by_user is None:
            raise UserNotFoundError(cancelled_by_user_login)

        if not self._can_cancel_booking(booking=booking, cancelled_by_user=cancelled_by_user):
            raise BookingPermissionDeniedError(
                booking_user_login=user_login,
                room_slot_id=room_slot_id,
                booking_date=booking_date,
                user_login=cancelled_by_user_login,
            )

        with self.booking_repository.session.begin_nested():
            cancelled_booking = self.booking_repository.cancel_booking(
                user_login=user_login,
                room_slot_id=room_slot_id,
                booking_date=booking_date,
                cancelled_by_user_login=cancelled_by_user_login,
            )

        if cancelled_booking is None:
            raise BookingNotFoundError(
                user_login=user_login,
                room_slot_id=room_slot_id,
                booking_date=booking_date,
            )

        return cancelled_booking

    @staticmethod
    def _can_cancel_booking(*, booking: Booking, cancelled_by_user: User) -> bool:
        role = cancelled_by_user.role
        is_admin = role is not None and role.role == ADMIN_ROLE_NAME
        return is_admin or booking.user_login == cancelled_by_user.login
