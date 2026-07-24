from app.api.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.api.schemas.bookings import BookingCreateRequest, BookingResponse
from app.api.schemas.rooms import (
    RoomCreateRequest,
    RoomAvailabilityResponse,
    RoomResponse,
    RoomSlotAvailabilityResponse,
    RoomSlotResponse,
    RoomSlotsUpdateRequest,
    SlotTemplateResponse,
)
from app.api.schemas.users import UserResponse

__all__ = [
    "BookingCreateRequest",
    "BookingResponse",
    "LoginRequest",
    "RegisterRequest",
    "RoomAvailabilityResponse",
    "RoomCreateRequest",
    "RoomResponse",
    "RoomSlotAvailabilityResponse",
    "RoomSlotResponse",
    "RoomSlotsUpdateRequest",
    "SlotTemplateResponse",
    "TokenResponse",
    "UserResponse",
]
