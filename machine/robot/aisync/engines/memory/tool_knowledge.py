from typing import TYPE_CHECKING, List, Optional, Sequence
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert

from core.db.session import Dialect, sessions
from core.db.transactional import Transactional
from core.db.utils import SessionContext

from ...db.collections import ToolCollection

if TYPE_CHECKING:
    from langchain_core.tools import BaseTool


class ToolKnowledge:
    def __init__(self, top_matches: Optional[int] = 2):
        self._top_matches = top_matches
        self.all_tools = []

    def add_tools(self, tools: Sequence["BaseTool"], embedder):
        for tool in tools:
            args_schema = {}
            for field_name in tool.args_schema.__fields__:
                args_schema[f"{field_name}"] = f"{tool.args_schema.__fields__[field_name].type_}"
            self.all_tools.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "args_schema": args_schema,
                    # Attempt to embed only description first
                    "embedding": embedder.embed_query(f"{tool.description}"),
                }
            )

    @SessionContext(dialect=Dialect.PGVECTOR)
    @Transactional(dialect=Dialect.PGVECTOR)
    async def save_tools(self) -> None:
        if len(self.all_tools) == 0:
            return
        session = sessions[Dialect.PGVECTOR].session
        # sessions[Dialect.PGVECTOR].set_session_context(str(uuid4()))
        # async with sessions[Dialect.PGVECTOR].session() as session:
        stmt = insert(ToolCollection).values(self.all_tools).returning(ToolCollection)
        await session.execute(stmt)
        # await session.commit()
        self.all_tools = []

    @SessionContext(dialect=Dialect.PGVECTOR)
    @Transactional(dialect=Dialect.PGVECTOR)
    async def remove_tools(self) -> None:
        # sessions[Dialect.PGVECTOR].set_session_context(str(uuid4()))
        session = sessions[Dialect.PGVECTOR].session
        # async with sessions[Dialect.PGVECTOR].session() as session:
        await session.execute(delete(ToolCollection))
        await session.commit()

    @SessionContext(dialect=Dialect.PGVECTOR)
    @Transactional(dialect=Dialect.PGVECTOR)
    async def find_relevant_tools(
        self, vectorized_input: List[float], tools_access: Sequence[str], tools: Sequence["BaseTool"]
    ) -> List["BaseTool"]:
        await self.save_tools()

        res = [tools["none_of_the_above"]]

        session = sessions[Dialect.PGVECTOR].session
        # DB Session for similarity search
        # sessions[Dialect.PGVECTOR].set_session_context(str(uuid4()))
        # async with sessions[Dialect.PGVECTOR].session() as session:
        # Top self._top_matches similarity search neighbors from input and output tables
        tool_match = await session.scalars(
            select(ToolCollection)
            .where(ToolCollection.name.in_(tools_access))
            .order_by(ToolCollection.embedding.l2_distance(vectorized_input))
            .limit(self._top_matches)
        )

        for tool in tool_match:
            if tool.name == "none_of_the_above":
                continue
            res.append(tools[tool.name])
        if len(res) == 1:
            res = []
        return res
