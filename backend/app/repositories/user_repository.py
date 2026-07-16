from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from app.models.role import Role
from app.models.user import User
from app.repositories.base import BaseRepository

# UserRepository contains CRUD operations over users.
# every user identified by a UUID, and every user has a login and a password hash.
class UserRepository(BaseRepository):
    def get_user_by_id(self, user_id: UUID) -> User | None:
        return self.session.get(User, user_id)

    def get_user_by_login(self, login: str) -> User | None:
        stmt = select(User).where(User.login == login)
        return self.session.scalar(stmt)

    # Update only the fields that were explicitly passed in.
    def update_user(
        self,
        *,
        user_id: UUID,
        login: str | None = None,
        password_hash: str | None = None,
        role: Role | None = None,
    ) -> User | None:
        user = self.get_user_by_id(user_id)
        if user is None:
            return None

        if login is not None:
            user.login = login
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
        user = User(
            login=login,
            password_hash=password_hash,
            role=role,
        )
        self.session.add(user)
        self.session.flush()
        return user

    def remove_user(self, *, user_id: UUID) -> None:
        user = self.get_user_by_id(user_id)
        if user is None:
            return

        self.session.delete(user)
        self.session.flush()
