from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import IdMixin

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.room import Room
    from app.models.slot_template import SlotTemplate


# Source of truth for which slots are valid for which rooms.
class RoomSlot(IdMixin, Base):
    __tablename__ = "room_slots"
    __table_args__ = (
        UniqueConstraint("room_id", "slot_template_id", name="uq_room_slots_room_id_slot_template_id"),
        Index("ix_room_slots_slot_template_id", "slot_template_id"),
    )

    room_id: Mapped[UUID] = mapped_column(
        ForeignKey("rooms.id", ondelete="RESTRICT"),
        nullable=False,
    )
    slot_template_id: Mapped[UUID] = mapped_column(
        ForeignKey("slot_templates.id", ondelete="RESTRICT"),
        nullable=False,
    )

    room: Mapped["Room"] = relationship(back_populates="room_slots")
    slot_template: Mapped["SlotTemplate"] = relationship(back_populates="room_slots")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="room_slot")
