from __future__ import annotations

from pydantic import BaseModel

from app.models.user import User


class UserResponse(BaseModel):
    login: str
    role: str

    @classmethod
    def from_user(cls, user: User) -> "UserResponse":
        return cls(
            login=user.login,
            role=user.role.role,
        )
