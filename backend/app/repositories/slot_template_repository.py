from __future__ import annotations

from datetime import time

from sqlalchemy import select

from app.models.room_slot import RoomSlot
from app.models.slot_template import SlotTemplate
from app.repositories.base import BaseRepository

class SlotTemplateRepository(BaseRepository):
    """SlotTemplateRepository owns the reusable time ranges used by room slots."""

    def list_slot_templates(self) -> list[SlotTemplate]:
        """Lists all slot templates in the database, ordered by start time and end time."""

        stmt = select(SlotTemplate).order_by(
            SlotTemplate.start_time.asc(),
            SlotTemplate.end_time.asc(),
        )
        return list(self.session.scalars(stmt))

    def get_slot_template_by_id(self, slot_template_id: int) -> SlotTemplate | None:
        """Retrieves a slot template by its ID. Returns None if not found."""

        return self.session.get(SlotTemplate, slot_template_id)

    def get_slot_template_by_time_range(
        self,
        *,
        start_time: time,
        end_time: time,
    ) -> SlotTemplate | None:
        """Retrieves a slot template by its start and end time. Returns None if not found."""

        stmt = select(SlotTemplate).where(
            SlotTemplate.start_time == start_time,
            SlotTemplate.end_time == end_time,
        )
        return self.session.scalar(stmt)

    def create_slot_template(self, *, start_time: time, end_time: time) -> SlotTemplate:
        """Creates a new slot template with the given start and end time, and returns the created SlotTemplate object."""

        slot_template = SlotTemplate(
            start_time=start_time,
            end_time=end_time,
        )
        self.session.add(slot_template)
        self.session.flush()
        return slot_template

    def remove_slot_template(self, *, slot_template_id: int) -> None:
        """Removes a slot template and all associated room slots from the database. If the slot template does not exist, nothing happens."""

        slot_template = self.get_slot_template_by_id(slot_template_id)
        if slot_template is None:
            return

        stmt = select(RoomSlot).where(RoomSlot.slot_template_id == slot_template_id)
        for room_slot in self.session.scalars(stmt):
            self.session.delete(room_slot)

        self.session.delete(slot_template)
        self.session.flush()
