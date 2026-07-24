from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.dependencies import get_booking_repository, get_booking_service, get_current_user
from app.api.errors import service_error_to_http
from app.api.schemas.bookings import BookingCreateRequest, BookingResponse
from app.models.user import User
from app.repositories.booking_repository import BookingRepository
from app.services.booking_service import BookingService
from app.services.errors import ServiceError


router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("/me", response_model=list[BookingResponse])
def list_my_bookings(
    current_user: Annotated[User, Depends(get_current_user)],
    booking_repository: Annotated[BookingRepository, Depends(get_booking_repository)],
    booking_date: Annotated[date | None, Query()] = None,
) -> list[BookingResponse]:
    bookings = booking_repository.list_bookings_for_user(
        user_login=current_user.login,
        booking_date=booking_date,
    )
    return [BookingResponse.from_booking(booking) for booking in bookings]


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    request: BookingCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    booking_service: Annotated[BookingService, Depends(get_booking_service)],
) -> BookingResponse:
    try:
        booking = booking_service.create_booking(
            room_slot_id=request.room_slot_id,
            booking_date=request.booking_date,
            user_login=current_user.login,
        )
    except ServiceError as exc:
        raise service_error_to_http(exc) from exc

    return BookingResponse.from_booking(booking)


@router.delete("/{room_slot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(
    room_slot_id: int,
    booking_date: Annotated[date, Query()],
    current_user: Annotated[User, Depends(get_current_user)],
    booking_service: Annotated[BookingService, Depends(get_booking_service)],
    user_login: Annotated[str | None, Query()] = None,
) -> Response:
    booking_user_login = user_login or current_user.login
    try:
        booking_service.cancel_booking(
            user_login=booking_user_login,
            room_slot_id=room_slot_id,
            booking_date=booking_date,
            cancelled_by_user_login=current_user.login,
        )
    except ServiceError as exc:
        raise service_error_to_http(exc) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
