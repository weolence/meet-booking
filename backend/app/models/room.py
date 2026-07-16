from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import IdMixin

if TYPE_CHECKING:
    from app.models.room_slot import RoomSlot


# Rooms only store the identifier used in booking flows.
class Room(IdMixin, Base):
    __tablename__ = "rooms"
    __table_args__ = (
        CheckConstraint("length(btrim(number)) > 0", name="rooms_number_not_blank"),
        UniqueConstraint("number", name="uq_rooms_number"),
    )

    number: Mapped[str] = mapped_column(String(32), nullable=False)

    room_slots: Mapped[list["RoomSlot"]] = relationship(back_populates="room")
