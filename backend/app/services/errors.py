from __future__ import annotations

from datetime import date, datetime
from uuid import UUID


class ServiceError(Exception):
    """Base class for service-layer business errors."""


class ValidationError(ServiceError):
    """Raised when input fails a business-level validation check."""


class NotFoundError(ServiceError):
    """Raised when the requested domain object does not exist."""


class ConflictError(ServiceError):
    """Raised when the requested change conflicts with current state."""


class PermissionDeniedError(ServiceError):
    """Raised when the current user cannot perform the requested action."""


class InvalidRoomNumberError(ValidationError):
    def __init__(self) -> None:
        super().__init__("Room number must not be blank.")


class InvalidCancellationError(ValidationError):
    def __init__(self, *, booking_id: UUID, cancelled_at: datetime, created_at: datetime) -> None:
        super().__init__(
            f"Booking {booking_id} cannot be cancelled at {cancelled_at.isoformat()} "
            f"before it was created at {created_at.isoformat()}."
        )


class RoomNotFoundError(NotFoundError):
    def __init__(self, room_id: UUID) -> None:
        super().__init__(f"Room {room_id} was not found.")


class RoomSlotNotFoundError(NotFoundError):
    def __init__(self, room_slot_id: UUID) -> None:
        super().__init__(f"Room slot {room_slot_id} was not found.")


class SlotTemplateNotFoundError(NotFoundError):
    def __init__(self, slot_template_id: UUID) -> None:
        super().__init__(f"Slot template {slot_template_id} was not found.")


class BookingNotFoundError(NotFoundError):
    def __init__(self, booking_id: UUID) -> None:
        super().__init__(f"Booking {booking_id} was not found.")


class UserNotFoundError(NotFoundError):
    def __init__(self, user_id: UUID) -> None:
        super().__init__(f"User {user_id} was not found.")


class InvalidCredentialsError(PermissionDeniedError):
    def __init__(self) -> None:
        super().__init__("Invalid login or password.")


class RoomAlreadyExistsError(ConflictError):
    def __init__(self, *, number: str) -> None:
        super().__init__(f"Room {number!r} already exists.")


class BookingConflictError(ConflictError):
    def __init__(self, *, room_slot_id: UUID, booking_date: date) -> None:
        super().__init__(
            f"Room slot {room_slot_id} is already booked on {booking_date.isoformat()}."
        )


class RoomHasBookingsError(ConflictError):
    def __init__(self, room_id: UUID) -> None:
        super().__init__(f"Room {room_id} cannot be removed because it has bookings.")


class RoomSlotInUseError(ConflictError):
    def __init__(self, room_id: UUID) -> None:
        super().__init__(
            f"Room {room_id} has room slots that cannot be removed because bookings exist for them."
        )


class BookingPermissionDeniedError(PermissionDeniedError):
    def __init__(self, *, booking_id: UUID, user_id: UUID) -> None:
        super().__init__(f"User {user_id} cannot cancel booking {booking_id}.")
