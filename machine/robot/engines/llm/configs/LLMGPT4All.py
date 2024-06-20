from typing import Any, List, Optional, Tuple, Type, Union

from langchain_community.llms import GPT4All
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableConfig

from core.logger import syslog

from .base import LLMConfig


class CustomizedGPT4All(GPT4All):
    max_tool_iter: Optional[int] = 10
    tool_name_to_tool: Optional[dict] = None

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

    """
    A version of create_tool_calling_agent that does not require the LLM to bind tools.
    Enable usage with Langchain's AgentExecutor.
    """

    def process_input(self, str_request: str) -> Tuple[Union[str, dict], bool]:
        try:
            str_request = str_request[str_request.index("{") :].strip()
            # syslog.info(f"\nProcessing Input Stage: {str_request}\n")
            res = JsonOutputParser().parse(str_request)
            if res is None:
                return f"Invalid input. Please try again.\n {e}", False
            return res, True
        except Exception as e:
            return f"Invalid input. Please try again.\n {e}", False

    def invoke_tool(self, input: Union[str, dict], config: Optional[RunnableConfig] = None) -> Tuple[str, bool]:
        """A function that we can use the perform a tool invocation.

        Args:
            tool_call_request: a dict that contains the keys name and arguments.
                The name must match the name of a tool that exists.
                The arguments are the arguments to that tool.
            config: This is configuration information that LangChain uses that contains
                things like callbacks, metadata, etc.See LCEL documentation about RunnableConfig.

        Returns:
            output from the requested tool
        """
        if isinstance(input, str):
            return (
                f"Action: Unidentified\nAction Input: Unidentified\nObservation:\
                \n -The input: ```\n{input}\n```\n was of an invalid dictionary format.\
                Please try again.\n",
                False,
            )
        try:
            tool_call_request = input
            name = tool_call_request["name"]
            requested_tool = self.tool_name_to_tool[name]
            res = requested_tool.invoke(tool_call_request["arguments"], config=config)
            syslog.info(res)
            return f"Action: {name}\nAction Input: {tool_call_request['arguments']}\nFinal Answer: {res}", True
        except Exception as e:
            return f"Action: Unidentified\nAction Input: Unidentified\nObservation: {e}", False

    def add_tools(self, tools):
        self.tool_name_to_tool = {tool.name: tool for tool in tools}

    def remove_tools(self):
        self.tool_name_to_tool = None

    def _should_continue(self, status, iterations):
        return not status and iterations < self.max_tool_iter

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        Override the GPT4All's _call method to handle tool invocation
        Currently only support one tool calling
        """
        # Return directly when there's no tools to use
        if self.tool_name_to_tool is None or len(self.tool_name_to_tool) == 0:
            return super()._call(prompt, stop, run_manager, **kwargs)
        # TODO: Implement the logic to break down tasks prior to calling function

        # Repeatedly calling the model until either the output is valid or it runs out of iteration
        tool_specs = None
        status = False
        iterations = 0
        while self._should_continue(status, iterations):
            tool_payload: str = super()._call(prompt, stop, run_manager, **kwargs)
            output, status = self.process_input(tool_payload)
            if iterations == 0:
                prompt += "\nError:\n"
            if isinstance(tool_specs, str):
                prompt += f"Iteration {iterations}: {tool_specs}\n"
            iterations += 1
            tool_specs = output

        # Invoke the tool
        tool_output, status = self.invoke_tool(tool_specs)
        return tool_output


class LLMGPT4All(LLMConfig):
    _pyclass: Type = CustomizedGPT4All

    model: str = "../gpt4all/mistral-7b-openorca.gguf2.Q4_0.gguf"
    # Change those configurations based on your device and desired speed
    device: str = "gpu"
    n_threads: int = 10
    temp: float = 0.4
