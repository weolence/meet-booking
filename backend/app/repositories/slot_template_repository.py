from __future__ import annotations

from datetime import time
from uuid import UUID

from sqlalchemy import select

from app.models.room_slot import RoomSlot
from app.models.slot_template import SlotTemplate
from app.repositories.base import BaseRepository


# SlotTemplateRepository owns the reusable time ranges used by room slots.
class SlotTemplateRepository(BaseRepository):
    def list_slot_templates(self) -> list[SlotTemplate]:
        stmt = select(SlotTemplate).order_by(
            SlotTemplate.start_time.asc(),
            SlotTemplate.end_time.asc(),
        )
        return list(self.session.scalars(stmt))

    def get_slot_template_by_id(self, slot_template_id: UUID) -> SlotTemplate | None:
        return self.session.get(SlotTemplate, slot_template_id)

    def get_slot_template_by_time_range(
        self,
        *,
        start_time: time,
        end_time: time,
    ) -> SlotTemplate | None:
        stmt = select(SlotTemplate).where(
            SlotTemplate.start_time == start_time,
            SlotTemplate.end_time == end_time,
        )
        return self.session.scalar(stmt)

    def create_slot_template(self, *, start_time: time, end_time: time) -> SlotTemplate:
        slot_template = SlotTemplate(
            start_time=start_time,
            end_time=end_time,
        )
        self.session.add(slot_template)
        self.session.flush()
        return slot_template

    def remove_slot_template(self, *, slot_template_id: UUID) -> None:
        slot_template = self.get_slot_template_by_id(slot_template_id)
        if slot_template is None:
            return

        stmt = select(RoomSlot).where(RoomSlot.slot_template_id == slot_template_id)
        for room_slot in self.session.scalars(stmt):
            self.session.delete(room_slot)

        self.session.delete(slot_template)
        self.session.flush()
