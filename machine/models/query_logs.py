from sqlalchemy import Column, Integer, String, JSON, Column, ForeignKey

from core.db import Base

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column
from pgvector.sqlalchemy import Vector


class QueryLogs(Base):
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, autoincrement=True) 
    payload = Column(JSON, nullable=False)
    embedding = mapped_column(Vector(1024), nullable=False)

