from datetime import datetime
from typing import Any, Dict, Optional

from core.logger import syslog

from ...aisync import tool


@tool
def get_today_date(tool_input: Optional[Any] = None, **kwargs: Any):
    """
    Get today's date.
    Reply to any question involve current date or time.
    Input is always None.
    """
    assistant = kwargs["assistant"]
    syslog.info(f"The tool's assistant is {assistant.name}")
    return datetime.today()


@tool
def get_my_name(tool_input: Optional[Any] = None, **kwargs: Any):
    """
    Get the assistant's name.
    Reply to any question involve the assistant's name.
    Input is always None.
    """
    assistant = kwargs["assistant"]
    syslog.info(f"The tool's assistant is {assistant.name}")
    return "Nhan Vo"


@tool
def none_of_the_above(tool_input: Optional[Dict] = None):
    """
    Use this tool if none of the above tools help.
    Input is always None.
    """
    return "STOP using tools and answer user's inquiry to the best of your ability WITHOUT tools."


@tool
def get_appstore_application_info(tool_input: Optional[Dict] = None):
    """
    Get information about an application in the App Store.
    Reply with a quotation about the application.
    Input is a URL to the application.
    """
    syslog.info(tool_input)
    return {
        "name": "Facebook",
        "description": "Facebook is a social media platform.",
        "platform": "",
        "feature": [],
        "location": [],
        "email": "",
        "type": "social media",
    }


@tool
def add(a: int, b: int):
    """
    Add two numbers.
    Input is two integers.
    """
    return a + b


@tool
def multiply(a: int, b: int):
    """
    Multiply two numbers.
    Input is two integers.
    """
    return a * b
