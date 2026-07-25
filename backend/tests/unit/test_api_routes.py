from __future__ import annotations

from collections.abc import Iterator
from datetime import time

import app.db.base  # noqa: F401
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.session import get_db_session
from app.main import create_app
from app.models.base import Base
from app.models.role import Role
from app.models.user import User
from app.repositories.room_repository import RoomRepository
from app.repositories.slot_template_repository import SlotTemplateRepository
from app.security.passwords import hash_password


@pytest.fixture()
def session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

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


@pytest.fixture()
def app(session: Session) -> FastAPI:
    app = create_app()

    def override_get_db_session() -> Iterator[Session]:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise

    app.dependency_overrides[get_db_session] = override_get_db_session
    return app


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


def create_user(
    session: Session,
    *,
    login: str,
    password: str = "secret-password",
    role_name: str = "user",
) -> User:
    role = Role(role=role_name)
    user = User(
        login=login,
        password_hash=hash_password(password),
        role=role,
    )
    session.add_all([role, user])
    session.flush()
    return user


def auth_headers(client: TestClient, *, login: str, password: str = "secret-password") -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={"login": login, "password": password},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_room_routes_allow_admin_to_manage_rooms_and_slots(
    client: TestClient,
    session: Session,
) -> None:
    create_user(session, login="admin", role_name="admin")
    slot_template = SlotTemplateRepository(session).create_slot_template(
        start_time=time(9, 0),
        end_time=time(10, 0),
    )
    session.commit()
    headers = auth_headers(client, login="admin")

    create_response = client.post(
        "/rooms",
        json={"name": " 301 "},
        headers=headers,
    )
    assert create_response.status_code == 201
    assert create_response.json()["name"] == "301"
    room_id = create_response.json()["id"]

    update_slots_response = client.put(
        f"/rooms/{room_id}/slots",
        json={"slot_template_ids": [slot_template.id]},
        headers=headers,
    )
    assert update_slots_response.status_code == 200
    room_slot = update_slots_response.json()[0]
    assert room_slot["room"]["id"] == room_id
    assert room_slot["slot_template"]["id"] == slot_template.id

    room_slots_response = client.get(
        f"/rooms/{room_id}/slots",
        headers=headers,
    )
    assert room_slots_response.status_code == 200
    assert room_slots_response.json() == [room_slot]

    rooms_response = client.get("/rooms", headers=headers)
    assert rooms_response.status_code == 200
    assert rooms_response.json() == [{"id": room_id, "name": "301"}]


def test_room_create_requires_admin_role(client: TestClient, session: Session) -> None:
    create_user(session, login="user")
    session.commit()
    headers = auth_headers(client, login="user")

    response = client.post(
        "/rooms",
        json={"name": "401"},
        headers=headers,
    )

    assert response.status_code == 403


def test_booking_routes_create_list_and_cancel_own_booking(
    client: TestClient,
    session: Session,
) -> None:
    create_user(session, login="booker")
    room_repository = RoomRepository(session)
    slot_template_repository = SlotTemplateRepository(session)
    room = room_repository.create_room(name="501")
    slot_template = slot_template_repository.create_slot_template(
        start_time=time(13, 0),
        end_time=time(14, 0),
    )
    room_slot = room_repository.create_room_slot(
        room_id=room.id,
        slot_template_id=slot_template.id,
    )
    session.commit()
    headers = auth_headers(client, login="booker")

    availability_response = client.get(
        f"/rooms/{room.id}/availability",
        params={"booking_date": "2026-07-17"},
        headers=headers,
    )
    assert availability_response.status_code == 200
    assert availability_response.json() == [
        {
            "room_slot": {
                "id": room_slot.id,
                "room": {"id": room.id, "name": "501"},
                "slot_template": {
                    "id": slot_template.id,
                    "start_time": "13:00:00",
                    "end_time": "14:00:00",
                },
            },
            "is_available": True,
        }
    ]

    all_availability_response = client.get(
        "/availability",
        params={"booking_date": "2026-07-17"},
        headers=headers,
    )
    assert all_availability_response.status_code == 200
    assert all_availability_response.json() == [
        {
            "room": {"id": room.id, "name": "501"},
            "slots": availability_response.json(),
        }
    ]

    create_response = client.post(
        "/bookings",
        json={"room_slot_id": room_slot.id, "booking_date": "2026-07-17"},
        headers=headers,
    )
    assert create_response.status_code == 201
    booking = create_response.json()
    assert booking["user_login"] == "booker"
    assert booking["room_slot_id"] == room_slot.id
    assert booking["booking_date"] == "2026-07-17"
    assert booking["cancelled_by_user_login"] is None

    list_response = client.get(
        "/bookings/me",
        params={"booking_date": "2026-07-17"},
        headers=headers,
    )
    assert list_response.status_code == 200
    assert list_response.json() == [booking]

    availability_response = client.get(
        f"/rooms/{room.id}/availability",
        params={"booking_date": "2026-07-17"},
        headers=headers,
    )
    assert availability_response.status_code == 200
    assert availability_response.json() == [
        {
            "room_slot": booking["room_slot"],
            "is_available": False,
        }
    ]

    all_availability_response = client.get(
        "/availability",
        params={"booking_date": "2026-07-17"},
        headers=headers,
    )
    assert all_availability_response.status_code == 200
    assert all_availability_response.json() == [
        {
            "room": {"id": room.id, "name": "501"},
            "slots": availability_response.json(),
        }
    ]

    cancel_response = client.delete(
        f"/bookings/{room_slot.id}",
        params={"booking_date": "2026-07-17"},
        headers=headers,
    )
    assert cancel_response.status_code == 204
