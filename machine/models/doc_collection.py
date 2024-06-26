from pgvector.sqlalchemy import Vector
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import mapped_column

from core.db import Base


class DocCollection(Base):
    __tablename__ = "doc_collection"

    id = mapped_column(UUID, primary_key=True)
    doc_metadata = mapped_column(JSONB, nullable=False)
    page_content = mapped_column(String, nullable=False)
    embedding = mapped_column(Vector(768), nullable=False)
