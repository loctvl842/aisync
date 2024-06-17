import json
from core.db.session import sessions, DBType
from sqlalchemy import select
from typing import Optional, Dict
from numpy.linalg import norm as l2_distance

from machine.models import ResponseLogs, QueryLogs


# TO clean up
from uuid import uuid4

class LongTermMemory():
  def __init__(self, top_matches: Optional[int] = 10):
    self._top_matches = top_matches

  async def save_interaction(self, input: str, output: str, vectorized_input, vectorized_output) -> None:
    sessions[DBType.PGVECTOR].set_session_context(str(uuid4()))
    async with sessions[DBType.PGVECTOR].session() as session:
      payload = {
          "input": input,
          "output": output,
      }
      session.add(QueryLogs(payload=json.dumps(payload), embedding=vectorized_input))
      session.add(ResponseLogs(payload=json.dumps(payload), embedding=vectorized_output))
      await session.commit()

  def clear_memory(self) -> None:
    QueryLogs.__table__.drop(self._engine)
    ResponseLogs.__table__.drop(self._engine)

  async def similarity_search(self, vectorized_input) -> Dict[str, str]:
    res = {}
    res["long_term_memory"] = "## Past interaction:\n\n"
    # DB Session for similarity search
    sessions[DBType.PGVECTOR].set_session_context(str(uuid4()))
    async with sessions[DBType.PGVECTOR].session() as session:
      # Top self._top_matches similarity search neighbors from input and output tables
      input_match = await session.scalars(select(QueryLogs).order_by(QueryLogs.embedding.l2_distance(vectorized_input)).limit(self._top_matches))
      output_match = await session.scalars(select(ResponseLogs).order_by(ResponseLogs.embedding.l2_distance(vectorized_input)).limit(self._top_matches))
      
      result = list(input_match) + list(output_match)
      # Result sorted by l2 distance
      ordered_res = sorted(result, key=lambda x: l2_distance(x.embedding - vectorized_input))[:self._top_matches]
      
      for inter in ordered_res:
        payload = json.loads(inter.payload)
        res["long_term_memory"] += f'Human: {payload["input"]}\nAI: {payload["output"]}\n'
      await session.commit()
    return res
