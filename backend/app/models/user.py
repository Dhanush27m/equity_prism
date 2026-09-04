"""
Component: Backend -> Data Layer -> ORM model
Belongs to: every table that scopes data per-user (documents, portfolio_holdings,
watchlist_items) foreign-keys into this one.
Purpose: the user table. In the deployed app there is exactly one row (username="local")
— see app/api/deps.py's get_local_user — since the whole system runs as one shared user
behind the access-key gate rather than real multi-user accounts.
"""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, default="local")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
