from sqlalchemy import Column, Integer, String, JSON, Column, ForeignKey

from core.db import Base
from core.db.mixins import TimestampMixin

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, mapped_column
from pgvector.sqlalchemy import Vector


class Chatting(Base, TimestampMixin):
    __tablename__ = "chattings"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True, nullable=False)
    payload = Column(JSON, nullable=False)
    embedding = mapped_column(Vector(3), nullable=False)

