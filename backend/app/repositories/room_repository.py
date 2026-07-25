from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models.room import Room
from app.models.room_slot import RoomSlot
from app.models.slot_template import SlotTemplate
from app.repositories.base import BaseRepository

class RoomRepository(BaseRepository):
    """RoomRepository owns rooms and the room-slot links attached to them."""

    def get_room_by_id(self, room_id: int) -> Room | None:
        """Get a room by its ID. Returns None if the room does not exist."""

        return self.session.get(Room, room_id)

    def get_room_by_name(self, name: str) -> Room | None:
        """Get a room by its name. Returns None if the room does not exist."""

        stmt = select(Room).where(Room.name == name)
        return self.session.scalar(stmt)

    def create_room(self, *, name: str) -> Room:
        """Creates a new room with the given name and returns the created Room object."""

        room = Room(name=name)
        self.session.add(room)
        self.session.flush()
        return room

    def remove_room(self, *, room_id: int) -> None:
        """Removes a room and all its associated room slots from the database."""

        room = self.get_room_by_id(room_id)
        if room is None:
            return

        for room_slot in self.list_room_slots(room_id=room_id):
            self.session.delete(room_slot)

        self.session.delete(room)
        self.session.flush()

    def list_rooms(self) -> list[Room]:
        """Lists all rooms in the database, ordered by name."""

        stmt = select(Room).order_by(Room.name.asc())
        return list(self.session.scalars(stmt))

    def list_room_slots(self, *, room_id: int | None = None) -> list[RoomSlot]:
        """Lists all room slots, optionally filtered by room ID. Returns a list of RoomSlot objects."""

        stmt = (
            select(RoomSlot)
            .join(RoomSlot.room)
            .join(RoomSlot.slot_template)
            .options(
                joinedload(RoomSlot.room),
                joinedload(RoomSlot.slot_template),
            )
            .order_by(
                Room.name.asc(),
                SlotTemplate.start_time.asc(),
                SlotTemplate.end_time.asc(),
            )
        )

        if room_id is not None:
            stmt = stmt.where(RoomSlot.room_id == room_id)

        return list(self.session.scalars(stmt))

    def get_room_slot_by_id(self, room_slot_id: int) -> RoomSlot | None:
        """Retrieves a room slot by its ID, including the associated room and slot template. Returns None if not found."""

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
        room_id: int,
        slot_template_id: int,
    ) -> RoomSlot | None:
        """Retrieves a room slot by room ID and slot template ID, including the associated room and slot template. Returns None if not found."""

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

    def create_room_slot(self, *, room_id: int, slot_template_id: int) -> RoomSlot:
        """Creates a new room slot linking a room and a slot template, and returns the created RoomSlot object."""

        room_slot = RoomSlot(
            room_id=room_id,
            slot_template_id=slot_template_id,
        )
        self.session.add(room_slot)
        self.session.flush()
        return room_slot

    def remove_room_slot(self, *, room_id: int, slot_template_id: int) -> None:
        """Removes a room slot by room ID and slot template ID. If the room slot does not exist, nothing happens."""

        room_slot = self.get_room_slot(
            room_id=room_id,
            slot_template_id=slot_template_id,
        )
        if room_slot is None:
            return

        self.session.delete(room_slot)
        self.session.flush()
