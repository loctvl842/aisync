from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import mapped_column

from core.db import Base


class DocCollection(Base):
    __tablename__ = "doc_collection"

    id = mapped_column(UUID, primary_key=True, default=uuid4)
    key = mapped_column(String, unique=True)
    doc_metadata = mapped_column(JSONB, nullable=False)
    page_content = mapped_column(String, nullable=False)
    embedding = mapped_column(Vector(768), nullable=False)
    document_name = mapped_column(String, nullable=False)
    __table_args__ = (
        Index(
            "idx_doc_embedding_vector_l2_ops",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_l2_ops"},
        ),
        Index(
            "idx_doc_embedding_vector_l1_ops",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_l1_ops"},
        ),
        Index(
            "idx_doc_embedding_vector_ip_ops",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_ip_ops"},
        ),
        Index(
            "idx_doc_embedding_vector_cosine_ops",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
