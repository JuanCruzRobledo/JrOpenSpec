"""Mixins for SQLAlchemy models."""

import re
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class AuditMixin:
    """Mixin providing audit fields and soft-delete capabilities for all models."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    # Plain Integer, NULLABLE, NO foreign key — see ADR-004
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deleted_by: Mapped[int | None] = mapped_column(Integer, nullable=True)

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    def soft_delete(self, user_id: int | None = None) -> None:
        """Mark record as deleted without physical removal."""
        self.deleted_at = func.now()  # type: ignore[assignment]
        self.deleted_by = user_id
        self.is_active = False

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.deleted_at = None
        self.deleted_by = None
        self.is_active = True


class TableNameMixin:
    """Mixin that auto-generates __tablename__ from CamelCase class name to snake_case plural."""

    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        # CamelCase to snake_case
        name = re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", cls.__name__)
        name = re.sub(r"(?<=[A-Z])([A-Z][a-z])", r"_\1", name)
        name = name.lower()
        # Pluralize
        if name.endswith("y") and name[-2] not in "aeiou":
            return name[:-1] + "ies"
        if name.endswith(("s", "sh", "ch", "x", "z")):
            return name + "es"
        return name + "s"
