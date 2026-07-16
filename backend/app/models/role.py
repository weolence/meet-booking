from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import IdMixin

if TYPE_CHECKING:
    from app.models.user import User


# Lookup table for allowed user roles.
# It has a potential to be expanded in the future, more roles can be added.
class Role(IdMixin, Base):
    __tablename__ = "roles"
    __table_args__ = (
        CheckConstraint("length(btrim(name)) > 0", name="roles_name_not_blank"),
        UniqueConstraint("name", name="uq_roles_name"),
    )

    name: Mapped[str] = mapped_column(String(64), nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="role")
