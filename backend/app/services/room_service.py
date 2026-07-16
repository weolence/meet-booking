from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.models.room import Room
from app.models.room_slot import RoomSlot
from app.repositories.booking_repository import BookingRepository
from app.repositories.room_repository import RoomRepository
from app.repositories.slot_template_repository import SlotTemplateRepository
from app.services.errors import (
    InvalidRoomNumberError,
    RoomAlreadyExistsError,
    RoomHasBookingsError,
    RoomNotFoundError,
    RoomSlotInUseError,
    SlotTemplateNotFoundError,
)


class RoomService:
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
        return self.room_repository.list_rooms()

    def list_taken_room_slots(self, *, room_id: UUID, booking_date: date) -> list[RoomSlot]:
        self._require_room(room_id)
        return self.booking_repository.list_taken_room_slots(
            room_id=room_id,
            booking_date=booking_date,
        )
    
    def list_available_room_slots(self, *, room_id: UUID, booking_date: date) -> list[RoomSlot]:
        self._require_room(room_id)

        room_slots = self.room_repository.list_room_slots(room_id=room_id)
        taken_room_slot_ids = {
            taken_room_slot.id
            for taken_room_slot in self.booking_repository.list_taken_room_slots(
                room_id=room_id,
                booking_date=booking_date,
            )
        }

        return [room_slot for room_slot in room_slots if room_slot.id not in taken_room_slot_ids]

    def create_room(self, *, number: str) -> Room:
        normalized_number = number.strip()
        if not normalized_number:
            raise InvalidRoomNumberError()

        try:
            with self.room_repository.session.begin_nested():
                return self.room_repository.create_room(number=normalized_number)
        except IntegrityError as exc:
            raise RoomAlreadyExistsError(number=normalized_number) from exc

    def remove_room(self, *, room_id: UUID) -> None:
        self._require_room(room_id)

        try:
            with self.room_repository.session.begin_nested():
                self.room_repository.remove_room(room_id=room_id)
        except IntegrityError as exc:
            raise RoomHasBookingsError(room_id) from exc

    def set_available_room_slots(
        self,
        *,
        room_id: UUID,
        slot_template_ids: Iterable[UUID],
    ) -> list[RoomSlot]:
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

    def _require_room(self, room_id: UUID) -> Room:
        room = self.room_repository.get_room_by_id(room_id)
        if room is None:
            raise RoomNotFoundError(room_id)
        return room
