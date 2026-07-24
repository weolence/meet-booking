from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import IdMixin

if TYPE_CHECKING:
    from app.models.room_slot import RoomSlot

class Room(IdMixin, Base):
    """Room model represents a physical room that can be booked for meetings or events."""

    __tablename__ = "rooms"
    __table_args__ = (
        CheckConstraint("length(btrim(name)) > 0", name="rooms_name_not_blank"),
        UniqueConstraint("name", name="uq_rooms_name"),
    )

    name: Mapped[str] = mapped_column(String(128), nullable=False)

    room_slots: Mapped[list["RoomSlot"]] = relationship(back_populates="room")
