import json
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import select

from core.db.session import Dialect, sessions
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

    async def save_interaction(
        self, input: str, output: str, vectorized_input: List[float], vectorized_output: List[float]
    ) -> None:
        sessions[Dialect.PGVECTOR].set_session_context(str(uuid4()))
        async with sessions[Dialect.PGVECTOR].session() as session:
            payload = {
                "input": input,
                "output": output,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            session.add(QueryLogs(payload=json.dumps(payload), embedding=vectorized_input))
            session.add(ResponseLogs(payload=json.dumps(payload), embedding=vectorized_output))
            await session.commit()

    @stopwatch(prefix="Persist memory similarity search")
    async def similarity_search(self, vectorized_input: List[float]) -> Dict[str, str]:
        # TODO: Change to cosine distance
        res = {}
        res["persist_memory"] = "## Past interaction:\n\n"
        # DB Session for similarity search
        sessions[Dialect.PGVECTOR].set_session_context(str(uuid4()))
        async with sessions[Dialect.PGVECTOR].session() as session:
            # Top self._top_matches similarity search neighbors from input and output tables
            input_match = await session.scalars(
                select(QueryLogs)
                .order_by(self.similarity_metrics(QueryLogs.embedding, vectorized_input))
                .limit(self._top_matches)
            )
            output_match = await session.scalars(
                select(ResponseLogs)
                .order_by(self.similarity_metrics(ResponseLogs.embedding, vectorized_input))
                .limit(self._top_matches)
            )

            result = list(input_match) + list(output_match)

            # Ordered result by time
            ordered_res = sorted(
                result, key=lambda x: datetime.strptime(json.loads(x.payload)["timestamp"], "%Y-%m-%d %H:%M:%S")
            )

            for inter in ordered_res:
                payload = json.loads(inter.payload)
                res["persist_memory"] += f'At {payload["timestamp"]}:\n'
                res["persist_memory"] += f'- Human: {payload["input"]}\n- AI: {payload["output"]}\n\n'
            await session.commit()
        return res
