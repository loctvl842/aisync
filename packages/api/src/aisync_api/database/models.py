from sqlalchemy import UUID, String
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import DeclarativeBase

import uuid


class Base(DeclarativeBase):
    """Enhanced base class for SQLAlchemy models."""


class User(Base):
    __tablename__ = "auth_user"

    id = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    email = mapped_column(String, unique=True, index=True)
    hashed_password = mapped_column(String)
