from typing import Any, Dict, List, Optional
from uuid import UUID

from httpx import Client
from langchain_core.outputs import (
    ChatGeneration,
    LLMResult,
)
from langfuse.callback import CallbackHandler
from langfuse.callback.langchain import (
    _extract_raw_esponse,
    _parse_model,
    _parse_usage,
    _parse_usage_model,
)
from langfuse.client import StatefulSpanClient, StatefulTraceClient


def parse_usage(response: LLMResult):
    llm_usage = _parse_usage(response)

    # Logic to parse ChatOllama's token usage
    if llm_usage is None:
        if hasattr(response, "generations"):
            for generation in response.generations:
                for generation_chunk in generation:
                    message_chunk = getattr(generation_chunk, "message", {})

                    chunk_usage = getattr(message_chunk, "usage_metadata", None)

                    if chunk_usage:
                        llm_usage = _parse_usage_model(chunk_usage)
                        break
    return llm_usage


def parse_model(response: LLMResult):
    llm_model = _parse_model(response)
    # TODO: add any more parsing rule if needed
    return llm_model


class AISyncHandler(CallbackHandler):
    """
    Leverages Langfuse's Callback Handler and change the parse usage function to support ChatOllama
    """

    def __init__(
        self,
        public_key: str | None = None,
        secret_key: str | None = None,
        host: str | None = None,
        debug: bool = False,
        stateful_client: StatefulTraceClient | StatefulSpanClient | None = None,
        update_stateful_client: bool = False,
        session_id: str | None = None,
        user_id: str | None = None,
        trace_name: str | None = None,
        release: str | None = None,
        version: str | None = None,
        metadata: Dict[str, Any] | None = None,
        tags: List[str] | None = None,
        threads: int | None = None,
        flush_at: int | None = None,
        flush_interval: int | None = None,
        max_retries: int | None = None,
        timeout: int | None = None,
        enabled: bool | None = None,
        httpx_client: Client | None = None,
        sdk_integration: str | None = None,
    ) -> None:
        super().__init__(
            public_key,
            secret_key,
            host,
            debug,
            stateful_client,
            update_stateful_client,
            session_id,
            user_id,
            trace_name,
            release,
            version,
            metadata,
            tags,
            threads,
            flush_at,
            flush_interval,
            max_retries,
            timeout,
            enabled,
            httpx_client,
            sdk_integration,
        )
        if self.version is None:
            self.version = "v1"

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        try:
            self._log_debug_event("on_llm_end", run_id, parent_run_id, response=response, kwargs=kwargs)
            if run_id not in self.runs:
                raise Exception("Run not found, see docs what to do in this case.")
            else:
                generation = response.generations[-1][-1]
                extracted_response = (
                    self._convert_message_to_dict(generation.message)
                    if isinstance(generation, ChatGeneration)
                    else _extract_raw_esponse(generation)
                )

                llm_usage = parse_usage(response)

                # e.g. azure returns the model name in the response
                model = parse_model(response)
                self.runs[run_id] = self.runs[run_id].end(
                    output=extracted_response,
                    usage=llm_usage,
                    version=self.version,
                    input=kwargs.get("inputs"),
                    model=model,
                )

                self._update_trace_and_remove_state(run_id, parent_run_id, extracted_response)

        except Exception as e:
            self.log.exception(e)
