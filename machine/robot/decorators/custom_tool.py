import functools
import inspect
from typing import Any, Callable, Optional, Type, Union

from langchain.tools import BaseTool, StructuredTool, Tool
from langchain_core.callbacks.manager import Callbacks
from langchain_core.pydantic_v1 import BaseModel
from langchain_core.runnables import Runnable

from machine.robot.assistants.base import Assistant


class CustomTool(Tool):
    assistant: Assistant = None

    def set_assistant(self, assistant: Assistant):
        self.assistant = assistant

        if self.func is not None:
            cur_func = self.func

            @functools.wraps(cur_func)
            def wrapper(*args, **kwargs):
                kwargs["assistant"] = self.assistant
                return cur_func(*args, **kwargs)

            self.func = wrapper
        else:
            print("coroutine")
            cur_func = self.coroutine

            @functools.wraps(cur_func)
            async def wrapper(*args, **kwargs):
                kwargs["assistant"] = self.assistant
                return await cur_func(*args, **kwargs)

            self.coroutine = wrapper


class CustomStructuredTool(StructuredTool):
    assistant: Assistant = None

    def set_assistant(self, assistant: Assistant):
        self.assistant = assistant

        if self.func is not None:
            cur_func = self.func

            @functools.wraps(cur_func)
            def wrapper(*args, **kwargs):
                kwargs["assistant"] = self.assistant
                return cur_func(*args, **kwargs)

            self.func = wrapper
        else:
            print("coroutine")
            cur_func = self.coroutine

            @functools.wraps(cur_func)
            async def wrapper(*args, **kwargs):
                kwargs["assistant"] = self.assistant
                return await cur_func(*args, **kwargs)

            self.coroutine = wrapper


def custom_tool(
    *args: Union[str, Callable, Runnable],
    return_direct: bool = False,
    args_schema: Optional[Type[BaseModel]] = None,
    infer_schema: bool = True,
    assistant: Assistant = None,
) -> Callable:
    """Make tools out of functions, can be used with or without arguments.

    Args:
        *args: The arguments to the tool.
        return_direct: Whether to return directly from the tool rather
            than continuing the agent loop.
        args_schema: optional argument schema for user to specify
        infer_schema: Whether to infer the schema of the arguments from
            the function's signature. This also makes the resultant tool
            accept a dictionary input to its `run()` function.

    Requires:
        - Function must be of type (str) -> str
        - Function must have a docstring

    Examples:
        .. code-block:: python

            @custom_tool
            def search_api(query: str) -> str:
                # Searches the API for the query.
                return

            @custom_tool("search", return_direct=True)
            def search_api(query: str) -> str:
                # Searches the API for the query.
                return
    """

    def _make_with_name(tool_name: str) -> Callable:
        def _make_tool(dec_func: Union[Callable, Runnable]) -> BaseTool:
            if isinstance(dec_func, Runnable):
                runnable = dec_func

                if runnable.input_schema.schema().get("type") != "object":
                    raise ValueError("Runnable must have an object schema.")

                async def ainvoke_wrapper(callbacks: Optional[Callbacks] = None, **kwargs: Any) -> Any:
                    return await runnable.ainvoke(kwargs, {"callbacks": callbacks})

                def invoke_wrapper(callbacks: Optional[Callbacks] = None, **kwargs: Any) -> Any:
                    return runnable.invoke(kwargs, {"callbacks": callbacks})

                coroutine = ainvoke_wrapper
                func = invoke_wrapper
                schema: Optional[Type[BaseModel]] = runnable.input_schema
                description = repr(runnable)
            elif inspect.iscoroutinefunction(dec_func):
                coroutine = dec_func
                func = None
                schema = args_schema
                description = None
            else:
                coroutine = None
                func = dec_func
                schema = args_schema
                description = None

            if infer_schema or args_schema is not None:
                return CustomStructuredTool.from_function(
                    func,
                    coroutine,
                    name=tool_name,
                    description=description,
                    return_direct=return_direct,
                    args_schema=schema,
                    infer_schema=infer_schema,
                )
            # If someone doesn't want a schema applied, we must treat it as
            # a simple string->string function
            if func.__doc__ is None:
                raise ValueError(
                    "Function must have a docstring if " "description not provided and infer_schema is False."
                )
            return CustomTool(
                name=tool_name,
                func=func,
                description=f"{tool_name} tool",
                return_direct=return_direct,
                coroutine=coroutine,
            )

        return _make_tool

    if len(args) == 2 and isinstance(args[0], str) and isinstance(args[1], Runnable):
        return _make_with_name(args[0])(args[1])
    elif len(args) == 1 and isinstance(args[0], str):
        # if the argument is a string, then we use the string as the tool name
        # Example usage: @tool("search", return_direct=True)
        return _make_with_name(args[0])
    elif len(args) == 1 and callable(args[0]):
        # if the argument is a function, then we use the function name as the tool name
        # Example usage: @tool
        return _make_with_name(args[0].__name__)(args[0])
    elif len(args) == 0:
        # if there are no arguments, then we use the function name as the tool name
        # Example usage: @tool(return_direct=True)
        def _partial(func: Callable[[str], str]) -> BaseTool:
            return _make_with_name(func.__name__)(func)

        return _partial
    else:
        raise ValueError("Too many arguments for tool decorator")
