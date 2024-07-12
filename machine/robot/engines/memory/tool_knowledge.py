from typing import Optional
from uuid import uuid4

from sqlalchemy import delete, select

from core.db.session import Dialect, sessions
from machine.robot.db.collections import ToolCollection


class ToolKnowledge:
    def __init__(self, top_matches: Optional[int] = 2):
        self._top_matches = top_matches
        self.all_tools = []

    def add_tools(self, tools, embedder):
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

    async def save_tools(self) -> None:
        if len(self.all_tools) == 0:
            return
        sessions[Dialect.PGVECTOR].set_session_context(str(uuid4()))
        async with sessions[Dialect.PGVECTOR].session() as session:
            for tool_dict in self.all_tools:
                session.add(
                    ToolCollection(
                        embedding=tool_dict["embedding"],
                        name=tool_dict["name"],
                        description=tool_dict["description"],
                        args_schema=tool_dict["args_schema"],
                    )
                )
            await session.commit()
        self.all_tools = []

    async def remove_tools(self):
        sessions[Dialect.PGVECTOR].set_session_context(str(uuid4()))
        async with sessions[Dialect.PGVECTOR].session() as session:
            await session.execute(delete(ToolCollection))
            await session.commit()

    async def find_relevant_tools(self, vectorized_input, tools_access, tools):
        await self.save_tools()
        # TODO: Change to cosine distance
        res = [tools["none_of_the_above"]]
        # DB Session for similarity search
        sessions[Dialect.PGVECTOR].set_session_context(str(uuid4()))
        async with sessions[Dialect.PGVECTOR].session() as session:
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
            await session.commit()
        if len(res) == 1:
            res = []
        return res
