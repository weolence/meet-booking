from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.dependencies import (
    get_current_admin_user,
    get_current_user,
    get_room_service,
    get_slot_template_repository,
)
from app.api.errors import service_error_to_http
from app.api.schemas.rooms import (
    RoomAvailabilityResponse,
    RoomCreateRequest,
    RoomResponse,
    RoomSlotAvailabilityResponse,
    RoomSlotResponse,
    RoomSlotsUpdateRequest,
    SlotTemplateResponse,
)
from app.models.user import User
from app.repositories.slot_template_repository import SlotTemplateRepository
from app.services.errors import ServiceError
from app.services.room_service import RoomService


router = APIRouter(tags=["rooms"])


@router.get("/rooms", response_model=list[RoomResponse])
def list_rooms(
    _current_user: Annotated[User, Depends(get_current_user)],
    room_service: Annotated[RoomService, Depends(get_room_service)],
) -> list[RoomResponse]:
    return [RoomResponse.from_room(room) for room in room_service.list_rooms()]


@router.post("/rooms", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
def create_room(
    request: RoomCreateRequest,
    _current_admin: Annotated[User, Depends(get_current_admin_user)],
    room_service: Annotated[RoomService, Depends(get_room_service)],
) -> RoomResponse:
    try:
        room = room_service.create_room(name=request.name)
    except ServiceError as exc:
        raise service_error_to_http(exc) from exc

    return RoomResponse.from_room(room)


@router.delete("/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_room(
    room_id: int,
    _current_admin: Annotated[User, Depends(get_current_admin_user)],
    room_service: Annotated[RoomService, Depends(get_room_service)],
) -> Response:
    try:
        room_service.remove_room(room_id=room_id)
    except ServiceError as exc:
        raise service_error_to_http(exc) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/rooms/{room_id}/slots", response_model=list[RoomSlotResponse])
def list_room_slots(
    room_id: int,
    _current_user: Annotated[User, Depends(get_current_user)],
    room_service: Annotated[RoomService, Depends(get_room_service)],
) -> list[RoomSlotResponse]:
    try:
        room_slots = room_service.list_room_slots(room_id=room_id)
    except ServiceError as exc:
        raise service_error_to_http(exc) from exc

    return [RoomSlotResponse.from_room_slot(room_slot) for room_slot in room_slots]

@router.get("/rooms/{room_id}/availability", response_model=list[RoomSlotAvailabilityResponse])
def list_room_slot_availability(
    room_id: int,
    booking_date: date,
    _current_user: Annotated[User, Depends(get_current_user)],
    room_service: Annotated[RoomService, Depends(get_room_service)],
) -> list[RoomSlotAvailabilityResponse]:
    """returns bunch of slots with marks about availability."""

    try:
        availability_items = room_service.list_room_slot_availability(
            room_id=room_id,
            booking_date=booking_date,
        )
    except ServiceError as exc:
        raise service_error_to_http(exc) from exc

    return [
        RoomSlotAvailabilityResponse.from_room_slot_availability(availability)
        for availability in availability_items
    ]


@router.get("/availability", response_model=list[RoomAvailabilityResponse])
def list_availability(
    booking_date: Annotated[date, Query()],
    _current_user: Annotated[User, Depends(get_current_user)],
    room_service: Annotated[RoomService, Depends(get_room_service)],
) -> list[RoomAvailabilityResponse]:
    rooms = room_service.list_rooms()
    response: list[RoomAvailabilityResponse] = []

    for room in rooms:
        try:
            availability_items = room_service.list_room_slot_availability(
                room_id=room.id,
                booking_date=booking_date,
            )
        except ServiceError as exc:
            raise service_error_to_http(exc) from exc

        response.append(
            RoomAvailabilityResponse.from_room_availability(
                room=room,
                availability_items=availability_items,
            )
        )

    return response


@router.put("/rooms/{room_id}/slots", response_model=list[RoomSlotResponse])
def set_room_slots(
    room_id: int,
    request: RoomSlotsUpdateRequest,
    _current_admin: Annotated[User, Depends(get_current_admin_user)],
    room_service: Annotated[RoomService, Depends(get_room_service)],
) -> list[RoomSlotResponse]:
    """sets available slots for a room. if some slots are already taken, they will be ignored."""

    try:
        room_slots = room_service.set_room_slots(
            room_id=room_id,
            slot_template_ids=request.slot_template_ids,
        )
    except ServiceError as exc:
        raise service_error_to_http(exc) from exc

    return [RoomSlotResponse.from_room_slot(room_slot) for room_slot in room_slots]


@router.get("/slot-templates", response_model=list[SlotTemplateResponse])
def list_slot_templates(
    _current_user: Annotated[User, Depends(get_current_user)],
    slot_template_repository: Annotated[
        SlotTemplateRepository,
        Depends(get_slot_template_repository),
    ],
) -> list[SlotTemplateResponse]:
    return [
        SlotTemplateResponse.from_slot_template(slot_template)
        for slot_template in slot_template_repository.list_slot_templates()
    ]
