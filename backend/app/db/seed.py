from __future__ import annotations

from sqlalchemy.orm import Session

from app.config.roles import ADMIN_ROLE_NAME, SEEDED_ROLE_NAMES
from app.config.settings import Settings
from app.repositories.user_repository import UserRepository
from app.security.passwords import hash_password

def seed_database(session: Session, settings: Settings) -> None:
    """Seeds the database with initial data, including roles and an admin user."""

    user_repository = UserRepository(session)
    roles_by_name = {
        role_name: user_repository.get_or_create_role_by_name(role_name)
        for role_name in _role_names_to_seed(settings.default_user_role_name)
    }

    admin_login = settings.seed_admin_login.strip()
    if not admin_login:
        raise ValueError("SEED_ADMIN_LOGIN must not be blank.")

    if not settings.seed_admin_password.strip():
        raise ValueError("SEED_ADMIN_PASSWORD must not be blank.")

    admin_role = roles_by_name[ADMIN_ROLE_NAME]
    admin_user = user_repository.get_user_by_login(admin_login)
    if admin_user is None:
        user_repository.create_user(
            login=admin_login,
            password_hash=hash_password(settings.seed_admin_password),
            role=admin_role,
        )
        return

    if admin_user.role_id != admin_role.id:
        admin_user.role = admin_role
        session.flush()


def _role_names_to_seed(default_user_role_name: str) -> tuple[str, ...]:
    role_names: list[str] = []
    for role_name in (*SEEDED_ROLE_NAMES, default_user_role_name):
        normalized_role_name = role_name.strip()
        if not normalized_role_name:
            raise ValueError("DEFAULT_USER_ROLE_NAME must not be blank.")

        if normalized_role_name not in role_names:
            role_names.append(normalized_role_name)

    return tuple(role_names)
