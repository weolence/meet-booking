from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import IdMixin

if TYPE_CHECKING:
    from app.models.user import User

class Role(IdMixin, Base):
    """Lookup table for allowed user roles.
    It has a potential to be expanded in the future, more roles can be added.
    """

    __tablename__ = "roles"
    __table_args__ = (
        CheckConstraint("length(btrim(role)) > 0", name="roles_role_not_blank"),
        UniqueConstraint("role", name="uq_roles_role"),
    )

    role: Mapped[str] = mapped_column(String(64), nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="role")
