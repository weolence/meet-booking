from __future__ import annotations

from datetime import time
from typing import TYPE_CHECKING

from pydantic import BaseModel

from app.models.room import Room
from app.models.room_slot import RoomSlot
from app.models.slot_template import SlotTemplate

if TYPE_CHECKING:
    from app.services.room_service import RoomSlotAvailability


class RoomCreateRequest(BaseModel):
    name: str


class RoomResponse(BaseModel):
    id: int
    name: str

    @classmethod
    def from_room(cls, room: Room) -> "RoomResponse":
        return cls(id=room.id, name=room.name)


class SlotTemplateResponse(BaseModel):
    id: int
    start_time: time
    end_time: time

    @classmethod
    def from_slot_template(cls, slot_template: SlotTemplate) -> "SlotTemplateResponse":
        return cls(
            id=slot_template.id,
            start_time=slot_template.start_time,
            end_time=slot_template.end_time,
        )


class RoomSlotResponse(BaseModel):
    id: int
    room: RoomResponse
    slot_template: SlotTemplateResponse

    @classmethod
    def from_room_slot(cls, room_slot: RoomSlot) -> "RoomSlotResponse":
        return cls(
            id=room_slot.id,
            room=RoomResponse.from_room(room_slot.room),
            slot_template=SlotTemplateResponse.from_slot_template(room_slot.slot_template),
        )


class RoomSlotsUpdateRequest(BaseModel):
    slot_template_ids: list[int]


class RoomSlotAvailabilityResponse(BaseModel):
    room_slot: RoomSlotResponse
    is_available: bool

    @classmethod
    def from_room_slot_availability(
        cls,
        availability: RoomSlotAvailability,
    ) -> "RoomSlotAvailabilityResponse":
        return cls(
            room_slot=RoomSlotResponse.from_room_slot(availability.room_slot),
            is_available=availability.is_available,
        )


class RoomAvailabilityResponse(BaseModel):
    room: RoomResponse
    slots: list[RoomSlotAvailabilityResponse]

    @classmethod
    def from_room_availability(
        cls,
        room: Room,
        availability_items: list[RoomSlotAvailability],
    ) -> "RoomAvailabilityResponse":
        return cls(
            room=RoomResponse.from_room(room),
            slots=[
                RoomSlotAvailabilityResponse.from_room_slot_availability(availability)
                for availability in availability_items
            ],
        )
