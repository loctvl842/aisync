import json
from sqlalchemy import create_engine, text, select
from sqlalchemy.orm import sessionmaker 
from typing import Optional, Dict
from numpy.linalg import norm as l2_distance

from machine.models import ChatInput, ChatOutput

class LongTermMemory():
  def __init__(self, top_matches: Optional[int] = 10):
    self._top_matches = top_matches

    # TODO: Move engine to a different place
    self._engine = create_engine("postgresql://postgres:12345@localhost:5432/aisync")
    self._Session = sessionmaker(bind=self._engine)
    ChatInput.__table__.create(self._engine, checkfirst=True)
    ChatOutput.__table__.create(self._engine, checkfirst=True)

  def save_interaction(self, input: str, output: str, vectorized_input, vectorized_output) -> None:
    with self._Session() as session:
      payload = {
          "input": input,
          "output": output,
      }
      session.add(ChatInput(payload=json.dumps(payload), embedding=vectorized_input))
      session.add(ChatOutput(payload=json.dumps(payload), embedding=vectorized_output))
      session.commit()

  def clear_memory(self) -> None:
    ChatInput.__table__.drop(self._engine)
    ChatOutput.__table__.drop(self._engine)

  def similarity_search(self, vectorized_input) -> Dict[str, str]:
    res = {}
    res["long_term_memory"] = "## Past interaction:\n\n"

    # DB Session for similarity search
    with self._Session() as session:
      session.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))

      # Top self._top_matches similarity search neighbors from input and output tables
      input_match = session.scalars(select(ChatInput).order_by(ChatInput.embedding.l2_distance(vectorized_input)).limit(self._top_matches))
      output_match = session.scalars(select(ChatOutput).order_by(ChatOutput.embedding.l2_distance(vectorized_input)).limit(self._top_matches))
      
      result = list(input_match) + list(output_match)
      # Result sorted by l2 distance
      ordered_res = sorted(result, key=lambda x: l2_distance(x.embedding - vectorized_input))[:self._top_matches]
      
      for inter in ordered_res:
        payload = json.loads(inter.payload)
        res["long_term_memory"] += f'Human: {payload["input"]}\nAI: {payload["output"]}\n'
      session.commit()

    return res

        
    
      