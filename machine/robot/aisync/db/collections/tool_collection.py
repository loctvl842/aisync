from pgvector.sqlalchemy import Vector
from sqlalchemy import Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import mapped_column

from core.db import Base


class ToolCollection(Base):
    __tablename__ = "tool_collection"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    name = mapped_column(String, nullable=False)
    description = mapped_column(String, nullable=False)
    args_schema = mapped_column(JSONB, nullable=False)
    embedding = mapped_column(Vector(768), nullable=False)

    __table_args__ = (
        Index(
            "idx_tool_embedding_vector_l2_ops",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_l2_ops"},
        ),
        Index(
            "idx_tool_embedding_vector_l1_ops",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_l1_ops"},
        ),
        Index(
            "idx_tool_embedding_vector_ip_ops",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_ip_ops"},
        ),
        Index(
            "idx_tool_embedding_vector_cosine_ops",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
