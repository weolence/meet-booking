from __future__ import annotations

from collections.abc import Iterator
from datetime import date, time

import app.db.base  # noqa: F401
import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session

from app.models.base import Base
from app.models.role import Role
from app.models.user import User
from app.repositories import BookingRepository, RoomRepository, SlotTemplateRepository, UserRepository
from app.services import (
    ActiveBookingNotFoundError,
    BookingConflictError,
    BookingPermissionDeniedError,
    BookingService,
    RoomHasBookingsError,
    RoomService,
    RoomSlotInUseError,
)


@pytest.fixture()
def session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _configure_sqlite(dbapi_connection, _connection_record) -> None:
        dbapi_connection.create_function(
            "btrim",
            1,
            lambda value: value.strip() if value is not None else None,
        )
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

    Base.metadata.create_all(engine)

    with Session(engine, expire_on_commit=False) as session:
        yield session


def create_user(session: Session, *, login: str, role_name: str = "user") -> User:
    role = session.scalar(select(Role).where(Role.role == role_name))
    if role is None:
        role = Role(role=role_name)
        session.add(role)

    user = User(
        login=login,
        password_hash="hashed-password",
        role=role,
    )
    session.add(user)
    session.flush()
    return user


def create_services(session: Session) -> tuple[BookingService, RoomService]:
    booking_repository = BookingRepository(session)
    room_repository = RoomRepository(session)
    slot_template_repository = SlotTemplateRepository(session)
    user_repository = UserRepository(session)

    booking_service = BookingService(
        booking_repository=booking_repository,
        room_repository=room_repository,
        user_repository=user_repository,
    )
    room_service = RoomService(
        room_repository=room_repository,
        booking_repository=booking_repository,
        slot_template_repository=slot_template_repository,
    )

    return booking_service, room_service


def test_booking_service_creates_booking_for_existing_free_room_slot(session: Session) -> None:
    booking_service, _room_service = create_services(session)
    room_repository = RoomRepository(session)
    slot_template_repository = SlotTemplateRepository(session)
    user = create_user(session, login="booker")

    room = room_repository.create_room(name="101")
    slot_template = slot_template_repository.create_slot_template(
        start_time=time(9, 0),
        end_time=time(10, 0),
    )
    room_slot = room_repository.create_room_slot(
        room_id=room.id,
        slot_template_id=slot_template.id,
    )

    booking = booking_service.create_booking(
        room_slot_id=room_slot.id,
        booking_date=date(2026, 7, 15),
        user_login=user.login,
    )

    assert booking.room_slot_id == room_slot.id
    assert booking.user_login == user.login
    assert booking.cancelled_by_user_login is None


def test_booking_service_rejects_duplicate_active_booking_for_same_slot_and_date(
    session: Session,
) -> None:
    booking_service, _room_service = create_services(session)
    room_repository = RoomRepository(session)
    slot_template_repository = SlotTemplateRepository(session)
    first_user = create_user(session, login="booker-1")
    second_user = create_user(session, login="booker-2")

    room = room_repository.create_room(name="102")
    slot_template = slot_template_repository.create_slot_template(
        start_time=time(10, 0),
        end_time=time(11, 0),
    )
    room_slot = room_repository.create_room_slot(
        room_id=room.id,
        slot_template_id=slot_template.id,
    )

    booking_service.create_booking(
        room_slot_id=room_slot.id,
        booking_date=date(2026, 7, 15),
        user_login=first_user.login,
    )

    with pytest.raises(BookingConflictError):
        booking_service.create_booking(
            room_slot_id=room_slot.id,
            booking_date=date(2026, 7, 15),
            user_login=second_user.login,
        )


def test_booking_service_allows_user_to_cancel_own_booking(session: Session) -> None:
    booking_service, _room_service = create_services(session)
    room_repository = RoomRepository(session)
    slot_template_repository = SlotTemplateRepository(session)
    user = create_user(session, login="owner")

    room = room_repository.create_room(name="103")
    slot_template = slot_template_repository.create_slot_template(
        start_time=time(11, 0),
        end_time=time(12, 0),
    )
    room_slot = room_repository.create_room_slot(
        room_id=room.id,
        slot_template_id=slot_template.id,
    )
    booking = booking_service.create_booking(
        room_slot_id=room_slot.id,
        booking_date=date(2026, 7, 16),
        user_login=user.login,
    )

    cancelled_booking = booking_service.cancel_booking(
        user_login=booking.user_login,
        room_slot_id=booking.room_slot_id,
        booking_date=booking.booking_date,
        cancelled_by_user_login=user.login,
    )

    assert cancelled_booking.cancelled_by_user_login == user.login


def test_booking_service_allows_user_to_rebook_cancelled_slot(session: Session) -> None:
    booking_service, _room_service = create_services(session)
    room_repository = RoomRepository(session)
    slot_template_repository = SlotTemplateRepository(session)
    user = create_user(session, login="returning-owner")

    room = room_repository.create_room(name="103-B")
    slot_template = slot_template_repository.create_slot_template(
        start_time=time(11, 30),
        end_time=time(12, 30),
    )
    room_slot = room_repository.create_room_slot(
        room_id=room.id,
        slot_template_id=slot_template.id,
    )
    booking = booking_service.create_booking(
        room_slot_id=room_slot.id,
        booking_date=date(2026, 7, 16),
        user_login=user.login,
    )
    booking_service.cancel_booking(
        user_login=booking.user_login,
        room_slot_id=booking.room_slot_id,
        booking_date=booking.booking_date,
        cancelled_by_user_login=user.login,
    )

    rebooked_booking = booking_service.create_booking(
        room_slot_id=room_slot.id,
        booking_date=date(2026, 7, 16),
        user_login=user.login,
    )

    assert rebooked_booking.user_login == user.login
    assert rebooked_booking.room_slot_id == room_slot.id
    assert rebooked_booking.cancelled_by_user_login is None


def test_booking_service_allows_admin_to_cancel_another_users_booking(session: Session) -> None:
    booking_service, _room_service = create_services(session)
    room_repository = RoomRepository(session)
    slot_template_repository = SlotTemplateRepository(session)
    owner = create_user(session, login="owner")
    admin = create_user(session, login="admin-user", role_name="admin")

    room = room_repository.create_room(name="104")
    slot_template = slot_template_repository.create_slot_template(
        start_time=time(12, 0),
        end_time=time(13, 0),
    )
    room_slot = room_repository.create_room_slot(
        room_id=room.id,
        slot_template_id=slot_template.id,
    )
    booking = booking_service.create_booking(
        room_slot_id=room_slot.id,
        booking_date=date(2026, 7, 16),
        user_login=owner.login,
    )

    cancelled_booking = booking_service.cancel_booking(
        user_login=booking.user_login,
        room_slot_id=booking.room_slot_id,
        booking_date=booking.booking_date,
        cancelled_by_user_login=admin.login,
    )

    assert cancelled_booking.cancelled_by_user_login == admin.login


def test_booking_service_allows_admin_to_cancel_active_booking_by_slot_and_date(
    session: Session,
) -> None:
    booking_service, _room_service = create_services(session)
    room_repository = RoomRepository(session)
    slot_template_repository = SlotTemplateRepository(session)
    owner = create_user(session, login="slot-owner")
    admin = create_user(session, login="admin-slot-user", role_name="admin")

    room = room_repository.create_room(name="104-B")
    slot_template = slot_template_repository.create_slot_template(
        start_time=time(12, 30),
        end_time=time(13, 30),
    )
    room_slot = room_repository.create_room_slot(
        room_id=room.id,
        slot_template_id=slot_template.id,
    )
    booking_service.create_booking(
        room_slot_id=room_slot.id,
        booking_date=date(2026, 7, 16),
        user_login=owner.login,
    )

    cancelled_booking = booking_service.cancel_active_booking_for_room_slot(
        room_slot_id=room_slot.id,
        booking_date=date(2026, 7, 16),
        cancelled_by_user_login=admin.login,
    )

    assert cancelled_booking.user_login == owner.login
    assert cancelled_booking.cancelled_by_user_login == admin.login


def test_booking_service_blocks_user_from_cancelling_active_booking_by_slot_for_other_user(
    session: Session,
) -> None:
    booking_service, _room_service = create_services(session)
    room_repository = RoomRepository(session)
    slot_template_repository = SlotTemplateRepository(session)
    owner = create_user(session, login="slot-owner-2")
    other_user = create_user(session, login="slot-other-user")

    room = room_repository.create_room(name="104-C")
    slot_template = slot_template_repository.create_slot_template(
        start_time=time(12, 45),
        end_time=time(13, 45),
    )
    room_slot = room_repository.create_room_slot(
        room_id=room.id,
        slot_template_id=slot_template.id,
    )
    booking_service.create_booking(
        room_slot_id=room_slot.id,
        booking_date=date(2026, 7, 16),
        user_login=owner.login,
    )

    with pytest.raises(BookingPermissionDeniedError) as exc_info:
        booking_service.cancel_active_booking_for_room_slot(
            room_slot_id=room_slot.id,
            booking_date=date(2026, 7, 16),
            cancelled_by_user_login=other_user.login,
        )

    assert owner.login not in str(exc_info.value)


def test_booking_service_reports_missing_active_booking_by_slot_and_date(
    session: Session,
) -> None:
    booking_service, _room_service = create_services(session)
    create_user(session, login="admin-missing-slot", role_name="admin")

    with pytest.raises(ActiveBookingNotFoundError):
        booking_service.cancel_active_booking_for_room_slot(
            room_slot_id=999,
            booking_date=date(2026, 7, 16),
            cancelled_by_user_login="admin-missing-slot",
        )


def test_booking_service_blocks_user_from_cancelling_another_users_booking(
    session: Session,
) -> None:
    booking_service, _room_service = create_services(session)
    room_repository = RoomRepository(session)
    slot_template_repository = SlotTemplateRepository(session)
    owner = create_user(session, login="owner")
    other_user = create_user(session, login="other-user")

    room = room_repository.create_room(name="105")
    slot_template = slot_template_repository.create_slot_template(
        start_time=time(13, 0),
        end_time=time(14, 0),
    )
    room_slot = room_repository.create_room_slot(
        room_id=room.id,
        slot_template_id=slot_template.id,
    )
    booking = booking_service.create_booking(
        room_slot_id=room_slot.id,
        booking_date=date(2026, 7, 16),
        user_login=owner.login,
    )

    with pytest.raises(BookingPermissionDeniedError) as exc_info:
        booking_service.cancel_booking(
            user_login=booking.user_login,
            room_slot_id=booking.room_slot_id,
            booking_date=booking.booking_date,
            cancelled_by_user_login=other_user.login,
        )

    assert owner.login not in str(exc_info.value)


def test_room_service_lists_rooms_in_sorted_order(session: Session) -> None:
    _booking_service, room_service = create_services(session)
    room_repository = RoomRepository(session)

    room_repository.create_room(name="302")
    room_repository.create_room(name="101")
    room_repository.create_room(name="201")

    rooms = room_service.list_rooms()

    assert [room.name for room in rooms] == ["101", "201", "302"]


def test_room_service_lists_only_free_room_slots_for_room_and_date(session: Session) -> None:
    booking_service, room_service = create_services(session)
    room_repository = RoomRepository(session)
    slot_template_repository = SlotTemplateRepository(session)
    user = create_user(session, login="room-booker")

    room = room_repository.create_room(name="106")
    first_slot_template = slot_template_repository.create_slot_template(
        start_time=time(9, 0),
        end_time=time(10, 0),
    )
    second_slot_template = slot_template_repository.create_slot_template(
        start_time=time(10, 0),
        end_time=time(11, 0),
    )
    first_room_slot = room_repository.create_room_slot(
        room_id=room.id,
        slot_template_id=first_slot_template.id,
    )
    second_room_slot = room_repository.create_room_slot(
        room_id=room.id,
        slot_template_id=second_slot_template.id,
    )

    booking_service.create_booking(
        room_slot_id=first_room_slot.id,
        booking_date=date(2026, 7, 17),
        user_login=user.login,
    )

    availability_items = room_service.list_room_slot_availability(
        room_id=room.id,
        booking_date=date(2026, 7, 17),
    )

    assert [item.room_slot for item in availability_items if item.is_available] == [second_room_slot]


def test_room_service_creates_and_removes_room(session: Session) -> None:
    _booking_service, room_service = create_services(session)
    room_repository = RoomRepository(session)
    slot_template_repository = SlotTemplateRepository(session)

    room = room_service.create_room(name=" 107 ")
    slot_template = slot_template_repository.create_slot_template(
        start_time=time(14, 0),
        end_time=time(15, 0),
    )
    room_repository.create_room_slot(
        room_id=room.id,
        slot_template_id=slot_template.id,
    )

    room_service.remove_room(room_id=room.id)

    assert room_repository.get_room_by_id(room.id) is None
    assert room_repository.list_room_slots(room_id=room.id) == []
    assert slot_template_repository.get_slot_template_by_id(slot_template.id) == slot_template


def test_room_service_set_room_slots_replaces_room_slot_links(session: Session) -> None:
    _booking_service, room_service = create_services(session)
    room_repository = RoomRepository(session)
    slot_template_repository = SlotTemplateRepository(session)

    room = room_repository.create_room(name="108")
    first_slot_template = slot_template_repository.create_slot_template(
        start_time=time(9, 0),
        end_time=time(10, 0),
    )
    second_slot_template = slot_template_repository.create_slot_template(
        start_time=time(10, 0),
        end_time=time(11, 0),
    )
    third_slot_template = slot_template_repository.create_slot_template(
        start_time=time(11, 0),
        end_time=time(12, 0),
    )
    room_repository.create_room_slot(
        room_id=room.id,
        slot_template_id=first_slot_template.id,
    )

    updated_room_slots = room_service.set_room_slots(
        room_id=room.id,
        slot_template_ids=[third_slot_template.id, second_slot_template.id, second_slot_template.id],
    )

    assert [room_slot.slot_template_id for room_slot in updated_room_slots] == [
        second_slot_template.id,
        third_slot_template.id,
    ]


def test_room_service_prevents_removing_room_with_bookings(session: Session) -> None:
    booking_service, room_service = create_services(session)
    room_repository = RoomRepository(session)
    slot_template_repository = SlotTemplateRepository(session)
    user = create_user(session, login="room-owner")

    room = room_repository.create_room(name="109")
    slot_template = slot_template_repository.create_slot_template(
        start_time=time(15, 0),
        end_time=time(16, 0),
    )
    room_slot = room_repository.create_room_slot(
        room_id=room.id,
        slot_template_id=slot_template.id,
    )
    booking_service.create_booking(
        room_slot_id=room_slot.id,
        booking_date=date(2026, 7, 18),
        user_login=user.login,
    )

    with pytest.raises(RoomHasBookingsError):
        room_service.remove_room(room_id=room.id)

    assert room_repository.get_room_by_id(room.id) == room


def test_room_service_prevents_removing_booked_room_slot_when_syncing_slots(
    session: Session,
) -> None:
    booking_service, room_service = create_services(session)
    room_repository = RoomRepository(session)
    slot_template_repository = SlotTemplateRepository(session)
    user = create_user(session, login="room-slot-owner")

    room = room_repository.create_room(name="110")
    first_slot_template = slot_template_repository.create_slot_template(
        start_time=time(16, 0),
        end_time=time(17, 0),
    )
    second_slot_template = slot_template_repository.create_slot_template(
        start_time=time(17, 0),
        end_time=time(18, 0),
    )
    first_room_slot = room_repository.create_room_slot(
        room_id=room.id,
        slot_template_id=first_slot_template.id,
    )
    second_room_slot = room_repository.create_room_slot(
        room_id=room.id,
        slot_template_id=second_slot_template.id,
    )
    booking_service.create_booking(
        room_slot_id=first_room_slot.id,
        booking_date=date(2026, 7, 18),
        user_login=user.login,
    )

    with pytest.raises(RoomSlotInUseError):
        room_service.set_room_slots(
            room_id=room.id,
            slot_template_ids=[second_slot_template.id],
        )

    assert room_repository.list_room_slots(room_id=room.id) == [first_room_slot, second_room_slot]
