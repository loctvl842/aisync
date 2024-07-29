import json
from datetime import datetime
from typing import Dict, List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import select

import core.utils as ut
from core.db.session import Dialect, sessions
from core.db.transactional import Transactional
from core.db.utils import SessionContext
from core.logger import syslog
from core.utils.decorators import stopwatch

from ...db.collections import QueryLogs, ResponseLogs


class PersistMemory:
    def __init__(self, top_matches: Optional[int] = 4):
        self._top_matches = top_matches
        self.similarity_metrics = getattr(Vector.comparator_factory, "l2_distance")

    def set_similarity_metrics(self, similarity_metrics: str) -> None:
        if not hasattr(Vector.comparator_factory, similarity_metrics):
            syslog.warning(
                f"Unsupported similarity metric for persist memory: {similarity_metrics}, using l2_distance instead"
            )
        self.similarity_metrics = getattr(Vector.comparator_factory, similarity_metrics, self.similarity_metrics)

    @SessionContext(dialect=Dialect.PGVECTOR)
    @Transactional(dialect=Dialect.PGVECTOR)
    async def save_interaction(
        self, input: str, output: str, vectorized_input: List[float], vectorized_output: List[float]
    ) -> None:
        session = sessions[Dialect.PGVECTOR].session
        payload = {
            "input": input,
            "output": output,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        session.add(QueryLogs(payload=json.dumps(payload), embedding=vectorized_input))
        session.add(ResponseLogs(payload=json.dumps(payload), embedding=vectorized_output))

    @SessionContext(dialect=Dialect.PGVECTOR)
    @Transactional(dialect=Dialect.PGVECTOR)
    async def similarity_search_query(self, vectorized_input: List[float]):
        session = sessions[Dialect.PGVECTOR].session
        stmt_query = (
            select(QueryLogs)
            .order_by(self.similarity_metrics(QueryLogs.embedding, vectorized_input))
            .limit(self._top_matches)
        )
        return await session.scalars(stmt_query)

    @SessionContext(dialect=Dialect.PGVECTOR)
    @Transactional(dialect=Dialect.PGVECTOR)
    async def similarity_search_response(self, vectorized_input: List[float]):
        session = sessions[Dialect.PGVECTOR].session
        stmt_response = (
            select(ResponseLogs)
            .order_by(self.similarity_metrics(ResponseLogs.embedding, vectorized_input))
            .limit(self._top_matches)
        )
        return await session.scalars(stmt_response)

    @SessionContext(dialect=Dialect.PGVECTOR)
    @Transactional(dialect=Dialect.PGVECTOR)
    @stopwatch(prefix="Persist memory similarity search")
    async def similarity_search(self, vectorized_input: List[float]) -> Dict[str, str]:
        # TODO: Change to cosine distance
        res = {}
        res["persist_memory"] = "## Past interaction:\n\n"
        # DB Session for similarity search
        session = sessions[Dialect.PGVECTOR].session
        # Top self._top_matches similarity search neighbors from input and output tables

        async def single_select(task: str, lock):
            if task == "query":
                return await self.similarity_search_query(vectorized_input)
            return await self.similarity_search_response(vectorized_input)

        query_match, response_match = await ut.parallel_do(["query", "response"], single_select)

        result = list(query_match) + list(response_match)

        # Ordered result by time
        ordered_res = sorted(
            result, key=lambda x: datetime.strptime(json.loads(x.payload)["timestamp"], "%Y-%m-%d %H:%M:%S")
        )

        for inter in ordered_res:
            payload = json.loads(inter.payload)
            res["persist_memory"] += f'At {payload["timestamp"]}:\n'
            res["persist_memory"] += f'- Human: {payload["input"]}\n- AI: {payload["output"]}\n\n'
        return res
