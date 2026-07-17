from app.models.base import Base
from app.models.booking import Booking
from app.models.revoked_token import RevokedToken
from app.models.role import Role
from app.models.room import Room
from app.models.room_slot import RoomSlot
from app.models.slot_template import SlotTemplate
from app.models.user import User

__all__ = [
    "Base",
    "Booking",
    "RevokedToken",
    "Role",
    "Room",
    "RoomSlot",
    "SlotTemplate",
    "User",
]
