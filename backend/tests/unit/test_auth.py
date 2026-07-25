from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

import app.db.base  # noqa: F401
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.session import get_db_session
from app.db.seed import seed_database
from app.main import create_app
from app.config.settings import Settings
from app.models.base import Base
from app.models.role import Role
from app.models.user import User
from app.repositories.room_repository import RoomRepository
from app.repositories.revoked_token_repository import RevokedTokenRepository
from app.repositories.user_repository import UserRepository
from app.security.passwords import hash_password, verify_password
from app.security.errors import InvalidAccessTokenError
from app.security.tokens import (
    create_access_token,
    decode_access_token,
    hash_access_token,
)
from app.services.auth_service import AuthService
from app.services.errors import InvalidCredentialsError, UserAlreadyExistsError


JWT_SECRET = "test-secret-with-at-least-32-bytes"


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


def create_user(
    session: Session,
    *,
    login: str = "booker",
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


def create_auth_service(session: Session) -> AuthService:
    return AuthService(
        UserRepository(session),
        RevokedTokenRepository(session),
        jwt_secret_key=JWT_SECRET,
        jwt_algorithm="HS256",
        access_token_expire_minutes=30,
        default_user_role_name="user",
    )


def create_settings(
    *,
    default_user_role_name: str = "user",
    seed_admin_login: str = "admin",
    seed_admin_password: str = "admin-password",
) -> Settings:
    return Settings(
        app_name="meet-booking-test",
        database_url="sqlite+pysqlite:///:memory:",
        db_echo=False,
        db_pool_size=1,
        db_max_overflow=0,
        default_user_role_name=default_user_role_name,
        seed_admin_login=seed_admin_login,
        seed_admin_password=seed_admin_password,
        jwt_secret_key=JWT_SECRET,
        jwt_algorithm="HS256",
        jwt_access_token_expire_minutes=30,
    )


def test_password_hash_verification_accepts_only_matching_password() -> None:
    password_hash = hash_password("correct-password")

    assert verify_password("correct-password", password_hash)
    assert not verify_password("wrong-password", password_hash)


def test_access_token_round_trip_returns_user_login() -> None:
    user_login = "booker"
    issued_at = datetime.now(timezone.utc).replace(microsecond=0)
    token = create_access_token(
        user_login=user_login,
        secret_key=JWT_SECRET,
        algorithm="HS256",
        expires_delta=timedelta(minutes=30),
        now=issued_at,
    )

    payload = decode_access_token(
        token=token,
        secret_key=JWT_SECRET,
        algorithm="HS256",
    )

    assert payload.user_login == user_login
    assert payload.expires_at == issued_at + timedelta(minutes=30)


def test_expired_access_token_is_rejected() -> None:
    token = create_access_token(
        user_login="booker",
        secret_key=JWT_SECRET,
        algorithm="HS256",
        expires_delta=timedelta(minutes=-1),
    )

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(
            token=token,
            secret_key=JWT_SECRET,
            algorithm="HS256",
        )


def test_auth_service_authenticates_user_and_issues_token(session: Session) -> None:
    user = create_user(session, login="booker", password="secret-password")
    auth_service = create_auth_service(session)

    authenticated_user = auth_service.authenticate_user(
        login="booker",
        password="secret-password",
    )
    token = auth_service.create_access_token_for_user(user=authenticated_user)
    token_payload = decode_access_token(
        token=token,
        secret_key=JWT_SECRET,
        algorithm="HS256",
    )

    assert authenticated_user == user
    assert token_payload.user_login == user.login


def test_auth_service_registers_default_user_role_with_hashed_password(session: Session) -> None:
    auth_service = create_auth_service(session)

    user = auth_service.register_user(
        login="  new-booker  ",
        password="secret-password",
    )

    assert user.login == "new-booker"
    assert user.role.role == "user"
    assert user.password_hash != "secret-password"
    assert verify_password("secret-password", user.password_hash)


def test_auth_service_rejects_duplicate_registration_login(session: Session) -> None:
    create_user(session, login="booker", password="secret-password")
    auth_service = create_auth_service(session)

    with pytest.raises(UserAlreadyExistsError):
        auth_service.register_user(login="booker", password="another-password")


def test_seed_database_creates_roles_and_admin_user(session: Session) -> None:
    settings = create_settings(seed_admin_login="root", seed_admin_password="admin-secret")

    seed_database(session, settings)

    user_repository = UserRepository(session)
    admin_user = user_repository.get_user_by_login("root")

    assert user_repository.get_role_by_name("user") is not None
    assert user_repository.get_role_by_name("admin") is not None
    assert admin_user is not None
    assert admin_user.role.role == "admin"
    assert verify_password("admin-secret", admin_user.password_hash)


def test_seed_database_creates_default_rooms_with_slots(session: Session) -> None:
    settings = create_settings()

    seed_database(session, settings)

    room_repository = RoomRepository(session)
    rooms = room_repository.list_rooms()

    assert [room.name for room in rooms] == ["101", "102", "103"]
    assert all(len(room_repository.list_room_slots(room_id=room.id)) == 8 for room in rooms)


def test_seed_database_is_idempotent_and_keeps_existing_admin_password(session: Session) -> None:
    settings = create_settings(seed_admin_login="root", seed_admin_password="admin-secret")
    seed_database(session, settings)
    admin_user = UserRepository(session).get_user_by_login("root")
    assert admin_user is not None
    original_password_hash = admin_user.password_hash

    seed_database(
        session,
        create_settings(seed_admin_login="root", seed_admin_password="changed-secret"),
    )

    assert UserRepository(session).get_user_by_login("root") == admin_user
    assert admin_user.password_hash == original_password_hash


def test_auth_service_logs_out_user_by_revoking_token(session: Session) -> None:
    user = create_user(session, login="booker", password="secret-password")
    auth_service = create_auth_service(session)
    access_token = auth_service.create_access_token_for_user(user=user)
    token_payload = decode_access_token(
        token=access_token,
        secret_key=JWT_SECRET,
        algorithm="HS256",
    )

    auth_service.logout_user(
        user=user,
        access_token=access_token,
        expires_at=token_payload.expires_at,
    )

    revoked_token_repository = RevokedTokenRepository(session)
    assert revoked_token_repository.is_token_revoked(hash_access_token(access_token))


def test_revoked_token_repository_removes_only_expired_tokens(session: Session) -> None:
    user = create_user(session, login="booker", password="secret-password")
    revoked_token_repository = RevokedTokenRepository(session)
    expired_token_hash = hash_access_token("expired-token")
    active_token_hash = hash_access_token("active-token")

    revoked_token_repository.revoke_token(
        token_hash=expired_token_hash,
        user_login=user.login,
        expires_at=datetime(2026, 7, 17, 8, tzinfo=timezone.utc),
    )
    revoked_token_repository.revoke_token(
        token_hash=active_token_hash,
        user_login=user.login,
        expires_at=datetime(2026, 7, 17, 10, tzinfo=timezone.utc),
    )

    removed_count = revoked_token_repository.remove_expired_tokens(
        now=datetime(2026, 7, 17, 9, tzinfo=timezone.utc),
    )

    assert removed_count == 1
    assert not revoked_token_repository.is_token_revoked(expired_token_hash)
    assert revoked_token_repository.is_token_revoked(active_token_hash)


def test_auth_service_rejects_invalid_credentials(session: Session) -> None:
    create_user(session, login="booker", password="secret-password")
    auth_service = create_auth_service(session)

    with pytest.raises(InvalidCredentialsError):
        auth_service.authenticate_user(login="booker", password="wrong-password")


def test_auth_routes_login_and_return_current_user(session: Session) -> None:
    user = create_user(
        session,
        login="admin",
        password="secret-password",
        role_name="admin",
    )
    app = create_app()

    def override_get_db_session() -> Iterator[Session]:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise

    app.dependency_overrides[get_db_session] = override_get_db_session
    client = TestClient(app)

    login_response = client.post(
        "/auth/login",
        json={"login": "admin", "password": "secret-password"},
    )
    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]
    me_response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert me_response.status_code == 200
    assert me_response.json() == {
        "login": "admin",
        "role": "admin",
    }


def test_auth_route_registers_user_and_allows_login(session: Session) -> None:
    app = create_app()

    def override_get_db_session() -> Iterator[Session]:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise

    app.dependency_overrides[get_db_session] = override_get_db_session
    client = TestClient(app)

    register_response = client.post(
        "/auth/register",
        json={"login": "booker", "password": "secret-password"},
    )
    assert register_response.status_code == 201
    assert register_response.json()["login"] == "booker"
    assert register_response.json()["role"] == "user"

    login_response = client.post(
        "/auth/login",
        json={"login": "booker", "password": "secret-password"},
    )

    assert login_response.status_code == 200
    assert login_response.json()["token_type"] == "bearer"


def test_auth_route_rejects_duplicate_registration_login(session: Session) -> None:
    create_user(session, login="booker", password="secret-password")
    app = create_app()

    def override_get_db_session() -> Iterator[Session]:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise

    app.dependency_overrides[get_db_session] = override_get_db_session
    client = TestClient(app)

    response = client.post(
        "/auth/register",
        json={"login": "booker", "password": "another-password"},
    )

    assert response.status_code == 409


def test_logout_revokes_current_access_token(session: Session) -> None:
    create_user(
        session,
        login="booker",
        password="secret-password",
        role_name="user",
    )
    app = create_app()

    def override_get_db_session() -> Iterator[Session]:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise

    app.dependency_overrides[get_db_session] = override_get_db_session
    client = TestClient(app)

    login_response = client.post(
        "/auth/login",
        json={"login": "booker", "password": "secret-password"},
    )
    access_token = login_response.json()["access_token"]

    logout_response = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    me_response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert logout_response.status_code == 204
    assert me_response.status_code == 401


def test_auth_route_rejects_invalid_login(session: Session) -> None:
    create_user(session, login="booker", password="secret-password")
    app = create_app()

    def override_get_db_session() -> Iterator[Session]:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise

    app.dependency_overrides[get_db_session] = override_get_db_session
    client = TestClient(app)

    response = client.post(
        "/auth/login",
        json={"login": "booker", "password": "wrong-password"},
    )

    assert response.status_code == 401
