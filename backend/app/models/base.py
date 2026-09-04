"""
Component: Backend -> Data Layer -> ORM base
Belongs to: imported by every model in app/models/*.
Purpose: the shared SQLAlchemy declarative base class, plus a reusable
created_at/updated_at mixin so timestamp columns aren't redefined on every model.
"""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# Base class every ORM model inherits from.
class Base(DeclarativeBase):
    pass


# Adds server-side-defaulted created_at/updated_at columns to any model that mixes it in.
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
