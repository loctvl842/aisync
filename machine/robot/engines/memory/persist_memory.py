import json
from datetime import datetime
from typing import Dict, Optional
from uuid import uuid4

from numpy.linalg import norm as l2_distance
from sqlalchemy import select

from core.db.session import Dialect, sessions
from machine.robot.models import QueryLogs, ResponseLogs


class PersistMemory:
    def __init__(self, top_matches: Optional[int] = 10):
        self._top_matches = top_matches

    async def save_interaction(self, input: str, output: str, vectorized_input, vectorized_output) -> None:
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

    async def similarity_search(self, vectorized_input) -> Dict[str, str]:
        # TODO: Change to cosine distance
        res = {}
        res["persist_memory"] = "## Past interaction:\n\n"
        # DB Session for similarity search
        sessions[Dialect.PGVECTOR].set_session_context(str(uuid4()))
        async with sessions[Dialect.PGVECTOR].session() as session:
            # Top self._top_matches similarity search neighbors from input and output tables
            input_match = await session.scalars(
                select(QueryLogs).order_by(QueryLogs.embedding.l2_distance(vectorized_input)).limit(self._top_matches)
            )
            output_match = await session.scalars(
                select(ResponseLogs)
                .order_by(ResponseLogs.embedding.l2_distance(vectorized_input))
                .limit(self._top_matches)
            )

            result = list(input_match) + list(output_match)
            # Result sorted by l2 distance
            ordered_res = sorted(result, key=lambda x: l2_distance(x.embedding - vectorized_input))[: self._top_matches]

            # Ordered result by time
            ordered_res = sorted(
                ordered_res, key=lambda x: datetime.strptime(json.loads(x.payload)["timestamp"], "%Y-%m-%d %H:%M:%S")
            )

            for inter in ordered_res:
                payload = json.loads(inter.payload)
                res["persist_memory"] += f'At {payload["timestamp"]}:\n'
                res["persist_memory"] += f'- Human: {payload["input"]}\n- AI: {payload["output"]}\n\n'
            await session.commit()
        return res
