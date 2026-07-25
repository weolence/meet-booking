from __future__ import annotations

from collections.abc import Iterator
from datetime import date, time

import app.db.base  # noqa: F401
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.models.role import Role
from app.models.user import User
from app.models.base import Base
from app.repositories import BookingRepository, RoomRepository, SlotTemplateRepository


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


def create_user(session: Session, *, login: str) -> User:
    role = Role(role=f"{login}-role")
    user = User(
        login=login,
        password_hash="hashed-password",
        role=role,
    )
    session.add_all([role, user])
    session.flush()
    return user


def test_room_repository_creates_room_slots_with_loaded_relations(session: Session) -> None:
    room_repository = RoomRepository(session)
    slot_template_repository = SlotTemplateRepository(session)

    slot_template = slot_template_repository.create_slot_template(
        start_time=time(9, 0),
        end_time=time(10, 0),
    )
    room = room_repository.create_room(name="101")
    room_slot = room_repository.create_room_slot(
        room_id=room.id,
        slot_template_id=slot_template.id,
    )

    fetched_room_slot = room_repository.get_room_slot_by_id(room_slot.id)

    assert fetched_room_slot is not None
    assert fetched_room_slot.room.name == "101"
    assert fetched_room_slot.slot_template.start_time == time(9, 0)
    assert room_repository.list_room_slots(room_id=room.id) == [fetched_room_slot]
    assert (
        slot_template_repository.get_slot_template_by_time_range(
            start_time=time(9, 0),
            end_time=time(10, 0),
        )
        == slot_template
    )


def test_room_repository_removes_only_requested_room_slot(session: Session) -> None:
    room_repository = RoomRepository(session)
    slot_template_repository = SlotTemplateRepository(session)

    room = room_repository.create_room(name="102")
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

    room_repository.remove_room_slot(
        room_id=room.id,
        slot_template_id=first_slot_template.id,
    )

    assert room_repository.get_room_slot_by_id(first_room_slot.id) is None
    assert room_repository.get_room_slot_by_id(second_room_slot.id) is not None
    assert room_repository.list_room_slots(room_id=room.id) == [second_room_slot]


def test_remove_room_cleans_up_room_slots_for_that_room(session: Session) -> None:
    room_repository = RoomRepository(session)
    slot_template_repository = SlotTemplateRepository(session)

    room = room_repository.create_room(name="201")
    slot_template = slot_template_repository.create_slot_template(
        start_time=time(13, 0),
        end_time=time(14, 0),
    )
    room_repository.create_room_slot(
        room_id=room.id,
        slot_template_id=slot_template.id,
    )

    room_repository.remove_room(room_id=room.id)

    assert room_repository.get_room_by_id(room.id) is None
    assert room_repository.list_room_slots() == []
    assert slot_template_repository.get_slot_template_by_id(slot_template.id) == slot_template


def test_remove_slot_template_cleans_up_room_slot_links(session: Session) -> None:
    room_repository = RoomRepository(session)
    slot_template_repository = SlotTemplateRepository(session)

    room = room_repository.create_room(name="301")
    slot_template = slot_template_repository.create_slot_template(
        start_time=time(15, 0),
        end_time=time(16, 0),
    )
    room_repository.create_room_slot(
        room_id=room.id,
        slot_template_id=slot_template.id,
    )

    slot_template_repository.remove_slot_template(slot_template_id=slot_template.id)

    assert slot_template_repository.get_slot_template_by_id(slot_template.id) is None
    assert room_repository.list_room_slots() == []
    assert room_repository.get_room_by_id(room.id) == room


def test_booking_repository_lists_only_active_taken_room_slots_for_room_and_date(
    session: Session,
) -> None:
    booking_repository = BookingRepository(session)
    room_repository = RoomRepository(session)
    slot_template_repository = SlotTemplateRepository(session)
    user = create_user(session, login="booker")

    room = room_repository.create_room(name="401")
    other_room = room_repository.create_room(name="402")
    first_slot_template = slot_template_repository.create_slot_template(
        start_time=time(9, 0),
        end_time=time(10, 0),
    )
    second_slot_template = slot_template_repository.create_slot_template(
        start_time=time(10, 0),
        end_time=time(11, 0),
    )
    room_slot = room_repository.create_room_slot(
        room_id=room.id,
        slot_template_id=first_slot_template.id,
    )
    cancelled_room_slot = room_repository.create_room_slot(
        room_id=room.id,
        slot_template_id=second_slot_template.id,
    )
    other_room_slot = room_repository.create_room_slot(
        room_id=other_room.id,
        slot_template_id=first_slot_template.id,
    )

    booking_repository.create_booking(
        room_slot_id=room_slot.id,
        booking_date=date(2026, 7, 15),
        user_login=user.login,
    )
    cancelled_booking = booking_repository.create_booking(
        room_slot_id=cancelled_room_slot.id,
        booking_date=date(2026, 7, 15),
        user_login=user.login,
    )
    booking_repository.create_booking(
        room_slot_id=other_room_slot.id,
        booking_date=date(2026, 7, 15),
        user_login=user.login,
    )
    booking_repository.create_booking(
        room_slot_id=cancelled_room_slot.id,
        booking_date=date(2026, 7, 16),
        user_login=user.login,
    )
    booking_repository.cancel_booking(
        user_login=cancelled_booking.user_login,
        room_slot_id=cancelled_booking.room_slot_id,
        booking_date=cancelled_booking.booking_date,
        cancelled_by_user_login=user.login,
    )

    taken_room_slots = booking_repository.list_active_bookings_for_date(
        room_id=room.id,
        booking_date=date(2026, 7, 15),
    )

    assert taken_room_slots == [room_slot]
