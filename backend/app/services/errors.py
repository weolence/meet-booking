from __future__ import annotations

from datetime import date


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


class InvalidRoomNameError(ValidationError):
    def __init__(self) -> None:
        super().__init__("Room name must not be blank.")


class RoomNotFoundError(NotFoundError):
    def __init__(self, room_id: int) -> None:
        super().__init__(f"Room {room_id} was not found.")


class RoomSlotNotFoundError(NotFoundError):
    def __init__(self, room_slot_id: int) -> None:
        super().__init__(f"Room slot {room_slot_id} was not found.")


class SlotTemplateNotFoundError(NotFoundError):
    def __init__(self, slot_template_id: int) -> None:
        super().__init__(f"Slot template {slot_template_id} was not found.")


class BookingNotFoundError(NotFoundError):
    def __init__(self, *, user_login: str, room_slot_id: int, booking_date: date) -> None:
        super().__init__(
            "Booking "
            f"(user_login={user_login}, room_slot_id={room_slot_id}, "
            f"booking_date={booking_date.isoformat()}) was not found."
        )


class ActiveBookingNotFoundError(NotFoundError):
    def __init__(self, *, room_slot_id: int, booking_date: date) -> None:
        super().__init__(
            "Active booking "
            f"(room_slot_id={room_slot_id}, booking_date={booking_date.isoformat()}) "
            "was not found."
        )


class UserNotFoundError(NotFoundError):
    def __init__(self, user_login: str) -> None:
        super().__init__(f"User {user_login!r} was not found.")


class InvalidCredentialsError(PermissionDeniedError):
    def __init__(self) -> None:
        super().__init__("Invalid login or password.")


class InvalidLoginError(ValidationError):
    def __init__(self) -> None:
        super().__init__("Login must not be blank.")


class InvalidPasswordError(ValidationError):
    def __init__(self) -> None:
        super().__init__("Password must not be blank.")


class UserAlreadyExistsError(ConflictError):
    def __init__(self, *, login: str) -> None:
        super().__init__(f"User {login!r} already exists.")


class RoomAlreadyExistsError(ConflictError):
    def __init__(self, *, name: str) -> None:
        super().__init__(f"Room {name!r} already exists.")


class BookingConflictError(ConflictError):
    def __init__(self, *, room_slot_id: int, booking_date: date) -> None:
        super().__init__(
            f"Room slot {room_slot_id} is already booked on {booking_date.isoformat()}."
        )


class RoomHasBookingsError(ConflictError):
    def __init__(self, room_id: int) -> None:
        super().__init__(f"Room {room_id} cannot be removed because it has bookings.")


class RoomSlotInUseError(ConflictError):
    def __init__(self, room_id: int) -> None:
        super().__init__(
            f"Room {room_id} has room slots that cannot be removed because bookings exist for them."
        )


class BookingPermissionDeniedError(PermissionDeniedError):
    def __init__(
        self,
        *,
        room_slot_id: int,
        booking_date: date,
        user_login: str,
    ) -> None:
        super().__init__(
            f"User {user_login!r} cannot cancel booking "
            f"room_slot_id={room_slot_id}, "
            f"booking_date={booking_date.isoformat()})."
        )
