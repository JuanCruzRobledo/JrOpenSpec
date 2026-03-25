"""Base model classes for all SQLAlchemy domain models."""

from sqlalchemy import BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from shared.models.mixins import AuditMixin, TableNameMixin


class Base(DeclarativeBase):
    """SQLAlchemy 2.0+ declarative base."""

    pass


class BaseModel(TableNameMixin, AuditMixin, Base):
    """Abstract base for all domain models. Provides id, audit fields, and auto table naming."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
