from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Column, Integer
from sqlalchemy.orm import mapped_column

from core.db import Base


class QueryLogs(Base):
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    payload = Column(JSON, nullable=False)
    embedding = mapped_column(Vector(768), nullable=False)
