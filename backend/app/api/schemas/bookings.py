from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from app.api.schemas.rooms import RoomSlotResponse
from app.models.booking import Booking


class BookingCreateRequest(BaseModel):
    room_slot_id: int
    booking_date: date


class BookingResponse(BaseModel):
    user_login: str
    room_slot_id: int
    booking_date: date
    room_slot: RoomSlotResponse
    cancelled_by_user_login: str | None

    @classmethod
    def from_booking(cls, booking: Booking) -> "BookingResponse":
        return cls(
            user_login=booking.user_login,
            room_slot_id=booking.room_slot_id,
            booking_date=booking.booking_date,
            room_slot=RoomSlotResponse.from_room_slot(booking.room_slot),
            cancelled_by_user_login=booking.cancelled_by_user_login,
        )
