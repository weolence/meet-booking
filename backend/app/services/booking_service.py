from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.models.booking import Booking
from app.models.user import User
from app.repositories.booking_repository import BookingRepository
from app.repositories.room_repository import RoomRepository
from app.repositories.user_repository import UserRepository
from app.services.errors import (
    BookingConflictError,
    BookingNotFoundError,
    BookingPermissionDeniedError,
    InvalidCancellationError,
    RoomSlotNotFoundError,
    UserNotFoundError,
)


ADMIN_ROLE_NAME = "admin"


class BookingService:
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
        room_slot_id: UUID,
        booking_date: date,
        user_id: UUID,
        created_at: datetime | None = None,
    ) -> Booking:
        user = self.user_repository.get_user_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)

        room_slot = self.room_repository.get_room_slot_by_id(room_slot_id)
        if room_slot is None:
            raise RoomSlotNotFoundError(room_slot_id)

        taken_room_slot_ids = {
            taken_room_slot.id
            for taken_room_slot in self.booking_repository.list_taken_room_slots(
                room_id=room_slot.room_id,
                booking_date=booking_date,
            )
        }
        if room_slot_id in taken_room_slot_ids:
            raise BookingConflictError(room_slot_id=room_slot_id, booking_date=booking_date)

        booking_created_at = created_at or datetime.now(timezone.utc)

        try:
            with self.booking_repository.session.begin_nested():
                return self.booking_repository.create_booking(
                    room_slot_id=room_slot_id,
                    booking_date=booking_date,
                    user_id=user.id,
                    created_at=booking_created_at,
                )
        except IntegrityError as exc:
            raise BookingConflictError(room_slot_id=room_slot_id, booking_date=booking_date) from exc

    def cancel_booking(
        self,
        *,
        booking_id: UUID,
        cancelled_by_user_id: UUID,
        cancelled_at: datetime | None = None,
    ) -> Booking:
        booking = self.booking_repository.get_booking_by_id(booking_id)
        if booking is None:
            raise BookingNotFoundError(booking_id)

        cancelled_by_user = self.user_repository.get_user_by_id(cancelled_by_user_id)
        if cancelled_by_user is None:
            raise UserNotFoundError(cancelled_by_user_id)

        if not self._can_cancel_booking(booking=booking, cancelled_by_user=cancelled_by_user):
            raise BookingPermissionDeniedError(booking_id=booking_id, user_id=cancelled_by_user_id)

        booking_cancelled_at = cancelled_at or datetime.now(timezone.utc)
        if booking_cancelled_at < booking.created_at:
            raise InvalidCancellationError(
                booking_id=booking.id,
                cancelled_at=booking_cancelled_at,
                created_at=booking.created_at,
            )

        with self.booking_repository.session.begin_nested():
            cancelled_booking = self.booking_repository.cancel_booking(
                booking_id=booking_id,
                cancelled_by_user_id=cancelled_by_user_id,
                cancelled_at=booking_cancelled_at,
            )

        if cancelled_booking is None:
            raise BookingNotFoundError(booking_id)

        return cancelled_booking

    @staticmethod
    def _can_cancel_booking(*, booking: Booking, cancelled_by_user: User) -> bool:
        role = cancelled_by_user.role
        is_admin = role is not None and role.name == ADMIN_ROLE_NAME
        return is_admin or booking.user_id == cancelled_by_user.id
