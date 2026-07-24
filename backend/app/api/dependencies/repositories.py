from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.repositories.booking_repository import BookingRepository
from app.repositories.revoked_token_repository import RevokedTokenRepository
from app.repositories.room_repository import RoomRepository
from app.repositories.slot_template_repository import SlotTemplateRepository
from app.repositories.user_repository import UserRepository


def get_user_repository(
    session: Annotated[Session, Depends(get_db_session)],
) -> UserRepository:
    return UserRepository(session)


def get_revoked_token_repository(
    session: Annotated[Session, Depends(get_db_session)],
) -> RevokedTokenRepository:
    return RevokedTokenRepository(session)


def get_room_repository(
    session: Annotated[Session, Depends(get_db_session)],
) -> RoomRepository:
    return RoomRepository(session)


def get_booking_repository(
    session: Annotated[Session, Depends(get_db_session)],
) -> BookingRepository:
    return BookingRepository(session)


def get_slot_template_repository(
    session: Annotated[Session, Depends(get_db_session)],
) -> SlotTemplateRepository:
    return SlotTemplateRepository(session)
