from __future__ import annotations

from sqlalchemy import select

from app.models.role import Role
from app.models.user import User
from app.repositories.base import BaseRepository

class UserRepository(BaseRepository):
    """UserRepository contains CRUD operations over users."""

    def get_user_by_login(self, login: str) -> User | None:
        """Get a user by their login. Returns None if the user does not exist."""

        return self.session.get(User, login)

    def get_role_by_name(self, role_name: str) -> Role | None:
        """Get a role by its name. Returns None if the role does not exist."""

        stmt = select(Role).where(Role.role == role_name)
        return self.session.scalar(stmt)

    def get_or_create_role_by_name(self, role_name: str) -> Role:
        """Get or create a role by its name. If the role does not exist, it will be created and returned."""

        role = self.get_role_by_name(role_name)
        if role is not None:
            return role

        role = Role(role=role_name)
        self.session.add(role)
        self.session.flush()
        return role

    def update_user(
        self,
        *,
        login: str,
        password_hash: str | None = None,
        role: Role | None = None,
    ) -> User | None:
        """Update only the fields that were explicitly passed in.
        If the user does not exist, returns None. Otherwise, returns the updated User object.
        """

        user = self.get_user_by_login(login)
        if user is None:
            return None

        if password_hash is not None:
            user.password_hash = password_hash
        if role is not None:
            user.role = role

        self.session.flush()
        return user

    def create_user(
        self,
        *,
        login: str,
        password_hash: str,
        role: Role,
    ) -> User:
        """Creates a new user with the given login, password hash, and role, and returns the created User object."""

        user = User(
            login=login,
            password_hash=password_hash,
            role=role,
        )
        self.session.add(user)
        self.session.flush()
        return user

    def remove_user(self, *, login: str) -> None:
        """Removes a user by their login. If the user does not exist, nothing happens."""

        user = self.get_user_by_login(login)
        if user is None:
            return

        self.session.delete(user)
        self.session.flush()
