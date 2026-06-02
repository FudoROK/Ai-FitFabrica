"""SQLAlchemy declarative base for portable persistence."""

from sqlalchemy.orm import DeclarativeBase


class SqlBase(DeclarativeBase):
    """Base metadata registry for portable SQL models."""
