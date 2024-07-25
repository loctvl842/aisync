from typing import TYPE_CHECKING, List, Literal, Optional

import numpy as np
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

import core.utils as utils
from core.logger import syslog
from core.utils.decorators import stopwatch

from ...engines.prompts import DEFAULT_BS_DETECTOR_SELF_REFLECTION_PROMPT
from ...utils import cosine_similarity_score, l1_score, l2_score, max_inner_product_score
from ..tracer import AISyncHandler

if TYPE_CHECKING:
    from ...engines.node import Node


class BSDetector:
    """
    A LLM response evaluator based on the trade-off of two main metrics: observed confidence and self reflection.
    Implemented based on the paper: https://arxiv.org/pdf/2308.16175
    """

    score_metric_mapping = {
        "l2_score": l2_score,
        "l1_score": l1_score,
        "cosine_similarity": cosine_similarity_score,
        "max_inner_product_score": max_inner_product_score,
    }

    self_reflection_threshold = {"excellent": 1.0, "good": 0.7, "fair": 0.3, "bad": 0}

    def __init__(
        self,
        confidence_threshold: Optional[float] = 0.5,
        embedding: Optional[Embeddings] = OpenAIEmbeddings(),
        llm: Optional[BaseChatModel] = ChatOpenAI(model="gpt-4o-mini"),
        sampling_temperature: Optional[float] = 1.0,
        self_reflection_temperature: Optional[float] = 0.2,
        k: Optional[int] = 5,
        alpha: Optional[float] = 0.8,
        beta: Optional[float] = 0.7,
        score_metric: Optional[
            Literal["l2_score", "l1_score", "cosine_similarity", "max_inner_product_score"]
        ] = "cosine_similarity",
    ):

        self.confidence_threshold = confidence_threshold
        self.embedding = embedding
        self.llm = llm
        self.sampling_temperature = sampling_temperature
        self.self_reflection_temperature = self_reflection_temperature
        self.k = k
        self.score_metric = score_metric
        self.alpha = alpha
        self.beta = beta

    @stopwatch(prefix="observed_consistency")
    async def observed_consistency(self, node: "Node", original_ans: str) -> float:

        self.llm.temperature = self.sampling_temperature
        original_ans_embedding = self.embedding.embed_query(original_ans)

        # samplign callback
        async def single_sample(node_state: tuple["Node", int], lock) -> float:
            node, index = node_state
            sampled_ans = node._chain.invoke(
                input=node.input,
                config={
                    "callbacks": [
                        AISyncHandler(
                            trace_name=f"Node: {node.name} (Observe Consistency {index})",
                            tags=[f"{node.assistant.suit.name}", "BSDetector"],
                        )
                    ]
                },
            )
            sampled_ans_embedding = self.embedding.embed_query(sampled_ans.content)

            s_i = BSDetector.score_metric_mapping[self.score_metric](original_ans_embedding, sampled_ans_embedding)
            r_i = 1 if sampled_ans.content.lower() == original_ans.lower() else 0
            o_i = self.alpha * s_i + (1 - self.alpha) * r_i
            syslog.info(f"r_i: {r_i}, o_i: {o_i}")
            return o_i

        # parallel sampling
        sampling_group = await utils.parallel_do([(node, i) for i in range(self.k)], single_sample)
        return np.mean(sampling_group)

    @stopwatch(prefix="self_reflection")
    def self_reflection(self, node: "Node", original_answer: str) -> float:
        # TODO: create a separate llm for self reflection
        self.llm.temperature = 0.1
        prompt = PromptTemplate.from_template(DEFAULT_BS_DETECTOR_SELF_REFLECTION_PROMPT)
        self_reflection_chain = prompt | self.llm
        assistant_prompt = node.get_prompt().format(**node.input)
        reflection = self_reflection_chain.invoke(
            {
                "assistant_prompt": assistant_prompt,
                "answer": original_answer,
                "choices": [*BSDetector.self_reflection_threshold.keys()],
                "top_choice": "excellent",
            },
            config={
                "callbacks": [
                    AISyncHandler(
                        trace_name=f"Node: {node.name} (Self Reflection)",
                        tags=[f"{node.assistant.suit.name}", "BSDetector"],
                    )
                ]
            },
        )
        choice = reflection.content.split(" ")[-1]
        for pos_choice in BSDetector.self_reflection_threshold.keys():
            if pos_choice.lower() in choice.lower():
                choice = pos_choice
                break
        if choice not in BSDetector.self_reflection_threshold.keys():
            syslog.warning(
                f"Unsupported self reflection choice: {choice}, using default value: {BSDetector.self_reflection_threshold['fair']}"
            )
        syslog.info(f"Choice: {choice}")
        syslog.info(f"Reflection: {reflection}")
        return utils.dig(BSDetector.self_reflection_threshold, f"{choice}", 0.3)

    @stopwatch(prefix="overall_confidence_estimate")
    async def overall_confidence_estimate(self, node: "Node", original_ans: str) -> float:
        observed_consistency = await self.observed_consistency(node, original_ans)
        self_reflection = self.self_reflection(node, original_ans)
        syslog.info(f"observed_consistency: {observed_consistency}, self_reflection: {self_reflection}")
        return self.beta * observed_consistency + (1 - self.beta) * self_reflection

    async def evaluate(self, node: "Node", original_ans: str) -> None:
        confidence_score = await self.overall_confidence_estimate(node, original_ans)
        if confidence_score >= self.confidence_threshold:
            syslog.info(f"LLM is confident about its answer ({confidence_score} >= {self.confidence_threshold})")
        else:
            syslog.warning(f"LLM is not confident about its answer ({confidence_score} < {self.confidence_threshold})")
