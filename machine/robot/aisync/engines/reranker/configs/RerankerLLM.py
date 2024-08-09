from functools import cmp_to_key
from typing import List, Literal, Optional, Type

from langchain_core.output_parsers import StrOutputParser

import core.utils as ut

from ....service import AISyncHandler
from ...llm import get_llm_object
from .base import AisyncReranker


class LLMReranker:
    """
    Implement based on this research paper: https://arxiv.org/pdf/2306.17563
    """

    # class RerankOptions(Enum):
    #     EXHAUSTIVE_RERANKING = "exhaustive_reranking"
    #     SORT_BASED_RERANKING = "sort_based_reranking"
    #     WINDOW_BASED_RERANKING = "window_based_reranking"

    RERANK_PROMPT = """
    You are an expert at reranking documents and output the most relevant document for the query.
    Given a query {query}, which of the following two passages is more relevant to the query?
    Passage A: {document_1}
    Passage B: {document_2}
    Output "Passage A" or "Passage B" or "Tie" if both passages are equally relevant:
    """

    def __init__(
        self,
        llm_name: str = Literal["LLMChatOllama", "LLMChatAnthropic", "LLMChatOpenAI", "LLMChatGoogleGenerativeAI"],
        llm_config: Optional[dict] = None,
        rerank_options: Optional[
            Literal["exhaustive_reranking", "sort_based_reranking", "window_based_reranking"]
        ] = "exhaustive_reranking",
        **kwargs,
    ):
        self.llm_name = llm_name
        self.llm_config = llm_config
        self.llm = get_llm_object((llm_name, llm_config))

        self.rerank_options = rerank_options
        self.set_rerank_prompt()
        self.set_rerank_chain()

    def set_rerank_prompt(self):
        from langchain.prompts import ChatPromptTemplate

        self.rerank_prompt = ChatPromptTemplate.from_messages([("system", LLMReranker.RERANK_PROMPT)])

    def set_rerank_chain(self):
        self.ranking_chain = self.rerank_prompt | self.llm | StrOutputParser()

    async def exhaustive_reranking(
        self, query: str, documents: List[str], top_k: Optional[int] = 3, batch_size: int = 32
    ):
        processed_input = [
            (query, {"corpus_id": i, "text": documents[i]}, {"corpus_id": j, "text": documents[j]})
            for i in range(len(documents))
            for j in range(i + 1, len(documents))
        ]

        results = [dict() for _ in range(len(documents))]
        for i in range(len(documents)):
            results[i]["corpus_id"] = i
            results[i]["text"] = documents[i]
            results[i]["score"] = 0

        async def score_document_pair(content: tuple[str | dict], lock):
            query, document_1, document_2 = content
            rerank_choice = self.ranking_chain.invoke(
                input={"query": query, "document_1": document_1["text"], "document_2": document_2["text"]},
                config={
                    "callbacks": [
                        AISyncHandler(
                            trace_name="exhaustive_reranking",
                            metadata={"query": query, "document_1": document_1, "document_2": document_2},
                            tags=["LLM Reranking"],
                        )
                    ]
                },
            )
            async with lock:
                if rerank_choice.lower() == "passage a":
                    results[document_1["corpus_id"]]["score"] += 1
                elif rerank_choice.lower() == "passage b":
                    results[document_2["corpus_id"]]["score"] += 1
                else:
                    results[document_1["corpus_id"]]["score"] += 0.5
                    results[document_2["corpus_id"]]["score"] += 0.5

        await ut.parallel_do(processed_input, score_document_pair, limit=batch_size)

        def comparator(a: dict, b: dict):
            if a["score"] > b["score"]:
                return -1
            elif a["score"] < b["score"]:
                return 1
            return 0

        sorted_results = sorted(results, key=cmp_to_key(comparator))
        return sorted_results[:top_k]

    def sort_based_reranking(self, query: str, documents: List[str], top_k: Optional[int] = 3, batch_size: int = 32):
        results = [dict() for _ in range(len(documents))]
        for i in range(len(documents)):
            results[i]["corpus_id"] = i
            results[i]["text"] = documents[i]
            results[i]["score"] = None

        def comparator(a: dict, b: dict):
            rerank_choice = self.ranking_chain.invoke(
                input={"query": query, "document_1": a["text"], "document_2": b["text"]},
                config={
                    "callbacks": [
                        AISyncHandler(
                            trace_name="sort_based_reranking",
                            metadata={"query": query, "document_1": a, "document_2": b},
                            tags=["LLM Reranking"],
                        )
                    ]
                },
            )
            if rerank_choice.lower() == "passage a":
                return -1
            elif rerank_choice.lower() == "passage b":
                return 1
            else:
                return 0

        sorted_results = sorted(results, key=cmp_to_key(comparator))

        return sorted_results[:top_k]

    def window_based_reranking(self, query: str, documents: List[str], top_k: Optional[int] = 3, batch_size: int = 32):
        results = [dict() for _ in range(len(documents))]
        for i in range(len(documents)):
            results[i]["corpus_id"] = i
            results[i]["text"] = documents[i]
            results[i]["score"] = 0

        def comparator(a: dict, b: dict):
            rerank_choice = self.ranking_chain.invoke(
                input={"query": query, "document_1": a["text"], "document_2": b["text"]},
                config={
                    "callbacks": [
                        AISyncHandler(
                            trace_name="window_based_reranking",
                            metadata={"query": query, "document_1": a, "document_2": b},
                            tags=["LLM Reranking"],
                        )
                    ]
                },
            )
            if rerank_choice.lower() == "passage a":
                return 1
            elif rerank_choice.lower() == "passage b":
                return -1
            else:
                return 0

        for i in range(top_k):
            ind = i
            for j in range(i + 1, len(documents)):
                if comparator(results[j], results[ind]) == 1:
                    ind = j
            results[ind], results[i] = results[i], results[ind]

        return results[:top_k]

    async def rank(self, query: str, documents: List[str], top_k: Optional[int] = 3, batch_size: int = 32, **kwargs):
        rank_function = getattr(self, self.rerank_options, None)
        if rank_function is None:
            raise ValueError(f"Invalid rerank option: {self.rerank_options}")
        from asyncio import iscoroutinefunction

        if iscoroutinefunction(rank_function):
            return await rank_function(query, documents, top_k, batch_size)
        return rank_function(query, documents, top_k, batch_size)


class RerankerLLM(AisyncReranker):
    _pyclass: Type = LLMReranker

    llm_name: Literal["LLMChatOllama", "LLMChatAnthropic", "LLMChatOpenAI", "LLMChatGoogleGenerativeAI"] = (
        "LLMChatOpenAI"
    )
    llm_config: Optional[dict] = None
    rerank_options: Optional[Literal["exhaustive_reranking", "sort_based_reranking", "window_based_reranking"]] = (
        "window_based_reranking"
    )
