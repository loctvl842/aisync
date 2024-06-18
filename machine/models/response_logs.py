from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column

from core.db import Base


class ResponseLogs(Base):
    __tablename__ = "response_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    payload = Column(JSON, nullable=False)
    embedding = mapped_column(Vector(768), nullable=False)
