from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models.room import Room
from app.models.room_slot import RoomSlot
from app.models.slot_template import SlotTemplate
from app.repositories.base import BaseRepository


# RoomRepository owns rooms and the room-slot links attached to them.
class RoomRepository(BaseRepository):
    def get_room_by_id(self, room_id: UUID) -> Room | None:
        return self.session.get(Room, room_id)

    def create_room(self, *, number: str) -> Room:
        room = Room(number=number)
        self.session.add(room)
        self.session.flush()
        return room

    def remove_room(self, *, room_id: UUID) -> None:
        room = self.get_room_by_id(room_id)
        if room is None:
            return

        for room_slot in self.list_room_slots(room_id=room_id):
            self.session.delete(room_slot)

        self.session.delete(room)
        self.session.flush()

    def list_rooms(self) -> list[Room]:
        stmt = select(Room).order_by(Room.number.asc())
        return list(self.session.scalars(stmt))

    def list_room_slots(self, *, room_id: UUID | None = None) -> list[RoomSlot]:
        stmt = (
            select(RoomSlot)
            .join(RoomSlot.room)
            .join(RoomSlot.slot_template)
            .options(
                joinedload(RoomSlot.room),
                joinedload(RoomSlot.slot_template),
            )
            .order_by(Room.number.asc(), SlotTemplate.start_time.asc(), SlotTemplate.end_time.asc())
        )

        if room_id is not None:
            stmt = stmt.where(RoomSlot.room_id == room_id)

        return list(self.session.scalars(stmt))

    def get_room_slot_by_id(self, room_slot_id: UUID) -> RoomSlot | None:
        stmt = (
            select(RoomSlot)
            .options(
                joinedload(RoomSlot.room),
                joinedload(RoomSlot.slot_template),
            )
            .where(RoomSlot.id == room_slot_id)
        )
        return self.session.scalar(stmt)

    def get_room_slot(
        self,
        *,
        room_id: UUID,
        slot_template_id: UUID,
    ) -> RoomSlot | None:
        stmt = (
            select(RoomSlot)
            .options(
                joinedload(RoomSlot.room),
                joinedload(RoomSlot.slot_template),
            )
            .where(
                RoomSlot.room_id == room_id,
                RoomSlot.slot_template_id == slot_template_id,
            )
        )
        return self.session.scalar(stmt)

    def create_room_slot(self, *, room_id: UUID, slot_template_id: UUID) -> RoomSlot:
        room_slot = RoomSlot(
            room_id=room_id,
            slot_template_id=slot_template_id,
        )
        self.session.add(room_slot)
        self.session.flush()
        return room_slot

    def remove_room_slot(self, *, room_id: UUID, slot_template_id: UUID) -> None:
        room_slot = self.get_room_slot(
            room_id=room_id,
            slot_template_id=slot_template_id,
        )
        if room_slot is None:
            return

        self.session.delete(room_slot)
        self.session.flush()
