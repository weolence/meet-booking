from __future__ import annotations

from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import IdMixin

if TYPE_CHECKING:
    from app.models.room_slot import RoomSlot

class SlotTemplate(IdMixin, Base):
    """Fixed time ranges used by the booking grid."""

    __tablename__ = "slot_templates"
    __table_args__ = (
        CheckConstraint("end_time > start_time", name="slot_templates_time_range"),
        UniqueConstraint(
            "start_time",
            "end_time",
            name="uq_slot_templates_start_time_end_time",
        ),
    )

    start_time: Mapped[time] = mapped_column(Time(timezone=False), nullable=False)
    end_time: Mapped[time] = mapped_column(Time(timezone=False), nullable=False)

    room_slots: Mapped[list["RoomSlot"]] = relationship(back_populates="slot_template")
