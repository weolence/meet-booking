from __future__ import annotations

from collections.abc import Iterator

import app.db.base  # noqa: F401
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.config.settings import Settings
from app.db.seed import seed_database
from app.db.session import get_db_session
from app.main import create_app
from app.models.base import Base


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
        seed_database(
            session=session,
            settings=Settings(
                app_name="meet-booking-test",
                database_url="sqlite+pysqlite:///:memory:",
                db_echo=False,
                db_pool_size=1,
                db_max_overflow=0,
                default_user_role_name="user",
                seed_admin_login="admin",
                seed_admin_password="admin",
                jwt_secret_key="test-secret-with-at-least-32-bytes",
                jwt_algorithm="HS256",
                jwt_access_token_expire_minutes=30,
            ),
        )
        session.commit()
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


def login(client: TestClient, *, login: str, password: str) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={"login": login, "password": password},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def register(client: TestClient, *, login: str, password: str) -> dict[str, str]:
    response = client.post(
        "/auth/register",
        json={"login": login, "password": password},
    )
    assert response.status_code == 201
    return {"login": login, "password": password}


def test_booking_flow_covers_availability_conflict_permissions_and_admin_cancel(
    client: TestClient,
) -> None:
    admin_headers = login(client, login="admin", password="admin")
    first_user = register(client, login="booker-1", password="secret-password")
    second_user = register(client, login="booker-2", password="secret-password")
    first_user_headers = login(client, **first_user)
    second_user_headers = login(client, **second_user)

    rooms_response = client.get("/rooms", headers=admin_headers)
    assert rooms_response.status_code == 200
    assert [room["name"] for room in rooms_response.json()] == ["101", "102", "103"]

    availability_response = client.get(
        "/availability",
        params={"booking_date": "2026-07-25"},
        headers=first_user_headers,
    )
    assert availability_response.status_code == 200
    assert len(availability_response.json()) == 3
    first_slot = availability_response.json()[0]["slots"][0]["room_slot"]

    create_response = client.post(
        "/bookings",
        json={"room_slot_id": first_slot["id"], "booking_date": "2026-07-25"},
        headers=first_user_headers,
    )
    assert create_response.status_code == 201
    assert create_response.json()["user_login"] == "booker-1"

    duplicate_response = client.post(
        "/bookings",
        json={"room_slot_id": first_slot["id"], "booking_date": "2026-07-25"},
        headers=second_user_headers,
    )
    assert duplicate_response.status_code == 409

    forbidden_cancel_response = client.delete(
        f"/bookings/{first_slot['id']}",
        params={"booking_date": "2026-07-25"},
        headers=second_user_headers,
    )
    assert forbidden_cancel_response.status_code == 403

    admin_cancel_response = client.delete(
        f"/bookings/{first_slot['id']}",
        params={"booking_date": "2026-07-25"},
        headers=admin_headers,
    )
    assert admin_cancel_response.status_code == 204

    availability_after_cancel_response = client.get(
        f"/rooms/{first_slot['room']['id']}/availability",
        params={"booking_date": "2026-07-25"},
        headers=first_user_headers,
    )
    assert availability_after_cancel_response.status_code == 200
    assert availability_after_cancel_response.json()[0]["is_available"]


def test_user_can_cancel_own_booking_without_owner_query(client: TestClient) -> None:
    register(client, login="owner", password="secret-password")
    headers = login(client, login="owner", password="secret-password")

    availability_response = client.get(
        "/availability",
        params={"booking_date": "2026-07-26"},
        headers=headers,
    )
    room_slot_id = availability_response.json()[0]["slots"][0]["room_slot"]["id"]

    create_response = client.post(
        "/bookings",
        json={"room_slot_id": room_slot_id, "booking_date": "2026-07-26"},
        headers=headers,
    )
    assert create_response.status_code == 201

    cancel_response = client.delete(
        f"/bookings/{room_slot_id}",
        params={"booking_date": "2026-07-26"},
        headers=headers,
    )
    assert cancel_response.status_code == 204
