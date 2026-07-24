from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

from sqlalchemy.exc import IntegrityError

from app.models.room import Room
from app.models.room_slot import RoomSlot
from app.repositories.booking_repository import BookingRepository
from app.repositories.room_repository import RoomRepository
from app.repositories.slot_template_repository import SlotTemplateRepository
from app.services.errors import (
    InvalidRoomNameError,
    RoomAlreadyExistsError,
    RoomHasBookingsError,
    RoomNotFoundError,
    RoomSlotInUseError,
    SlotTemplateNotFoundError,
)


@dataclass(frozen=True)
class RoomSlotAvailability:
    room_slot: RoomSlot
    is_available: bool

class RoomService:
    """Service for handling room and room slot management logic."""

    def __init__(
        self,
        room_repository: RoomRepository,
        booking_repository: BookingRepository,
        slot_template_repository: SlotTemplateRepository,
    ) -> None:
        self.room_repository = room_repository
        self.booking_repository = booking_repository
        self.slot_template_repository = slot_template_repository

    def list_rooms(self) -> list[Room]:
        """Lists all rooms in the system."""

        return self.room_repository.list_rooms()

    def list_room_slots(self, *, room_id: int) -> list[RoomSlot]:
        """Lists all room slots for a given room. Raises RoomNotFoundError if the room does not exist.
        """

        self._require_room(room_id)
        return self.room_repository.list_room_slots(room_id=room_id)

    def list_room_slot_availability(
        self,
        *,
        room_id: int,
        booking_date: date,
    ) -> list[RoomSlotAvailability]:
        """Makes an intersection of room slots and bookings to determine which room slots are available for a given room and date.
        Raises RoomNotFoundError if the room does not exist.
        """

        self._require_room(room_id)

        room_slots = self.room_repository.list_room_slots(room_id=room_id)
        taken_room_slot_ids = {
            taken_room_slot.id
            for taken_room_slot in self.booking_repository.list_active_bookings_for_date(
                room_id=room_id,
                booking_date=booking_date,
            )
        }

        return [
            RoomSlotAvailability(
                room_slot=room_slot,
                is_available=room_slot.id not in taken_room_slot_ids,
            )
            for room_slot in room_slots
        ]

    def create_room(self, *, name: str) -> Room:
        """Creates a new room with the given name. Raises InvalidRoomNameError if the name is empty or whitespace.
        Raises RoomAlreadyExistsError if a room with the same name already exists.
        """

        normalized_name = name.strip()
        if not normalized_name:
            raise InvalidRoomNameError()

        try:
            with self.room_repository.session.begin_nested():
                return self.room_repository.create_room(name=normalized_name)
        except IntegrityError as exc:
            raise RoomAlreadyExistsError(name=normalized_name) from exc

    def remove_room(self, *, room_id: int) -> None:
        """Removes a room by its ID. Raises RoomNotFoundError if the room does not exist.
        Raises RoomHasBookingsError if the room has any bookings associated with it.
        """

        self._require_room(room_id)

        try:
            with self.room_repository.session.begin_nested():
                self.room_repository.remove_room(room_id=room_id)
        except IntegrityError as exc:
            raise RoomHasBookingsError(room_id) from exc

    def set_room_slots(
        self,
        *,
        room_id: int,
        slot_template_ids: Iterable[int],
    ) -> list[RoomSlot]:
        """Sets the room slots for a given room. Raises RoomNotFoundError if the room does not exist.
        Raises SlotTemplateNotFoundError if any of the provided slot template IDs do not exist.
        Raises RoomSlotInUseError if any of the existing room slots are in use by bookings and cannot be removed.
        """

        self._require_room(room_id)

        desired_slot_template_ids = list(dict.fromkeys(slot_template_ids))
        for slot_template_id in desired_slot_template_ids:
            if self.slot_template_repository.get_slot_template_by_id(slot_template_id) is None:
                raise SlotTemplateNotFoundError(slot_template_id)

        existing_room_slots = self.room_repository.list_room_slots(room_id=room_id)
        existing_slot_template_ids = {
            room_slot.slot_template_id
            for room_slot in existing_room_slots
        }
        desired_slot_template_id_set = set(desired_slot_template_ids)

        slot_template_ids_to_remove = existing_slot_template_ids - desired_slot_template_id_set
        slot_template_ids_to_add = desired_slot_template_id_set - existing_slot_template_ids

        try:
            with self.room_repository.session.begin_nested():
                for slot_template_id in slot_template_ids_to_remove:
                    self.room_repository.remove_room_slot(
                        room_id=room_id,
                        slot_template_id=slot_template_id,
                    )

                for slot_template_id in slot_template_ids_to_add:
                    self.room_repository.create_room_slot(
                        room_id=room_id,
                        slot_template_id=slot_template_id,
                    )
        except IntegrityError as exc:
            raise RoomSlotInUseError(room_id) from exc

        return self.room_repository.list_room_slots(room_id=room_id)

    def _require_room(self, room_id: int) -> Room:
        room = self.room_repository.get_room_by_id(room_id)
        if room is None:
            raise RoomNotFoundError(room_id)
        return room
