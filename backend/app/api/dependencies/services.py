from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.dependencies.repositories import (
    get_booking_repository,
    get_revoked_token_repository,
    get_room_repository,
    get_slot_template_repository,
    get_user_repository,
)
from app.config.settings import Settings, get_settings
from app.repositories.booking_repository import BookingRepository
from app.repositories.revoked_token_repository import RevokedTokenRepository
from app.repositories.room_repository import RoomRepository
from app.repositories.slot_template_repository import SlotTemplateRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.booking_service import BookingService
from app.services.room_service import RoomService


def get_auth_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    revoked_token_repository: Annotated[
        RevokedTokenRepository,
        Depends(get_revoked_token_repository),
    ],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    return AuthService(
        user_repository,
        revoked_token_repository,
        jwt_secret_key=settings.jwt_secret_key,
        jwt_algorithm=settings.jwt_algorithm,
        access_token_expire_minutes=settings.jwt_access_token_expire_minutes,
        default_user_role_name=settings.default_user_role_name,
    )


def get_room_service(
    room_repository: Annotated[RoomRepository, Depends(get_room_repository)],
    booking_repository: Annotated[BookingRepository, Depends(get_booking_repository)],
    slot_template_repository: Annotated[
        SlotTemplateRepository,
        Depends(get_slot_template_repository),
    ],
) -> RoomService:
    return RoomService(
        room_repository=room_repository,
        booking_repository=booking_repository,
        slot_template_repository=slot_template_repository,
    )


def get_booking_service(
    booking_repository: Annotated[BookingRepository, Depends(get_booking_repository)],
    room_repository: Annotated[RoomRepository, Depends(get_room_repository)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> BookingService:
    return BookingService(
        booking_repository=booking_repository,
        room_repository=room_repository,
        user_repository=user_repository,
    )
