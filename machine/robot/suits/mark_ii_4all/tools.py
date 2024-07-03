from datetime import datetime
from typing import Any, Optional

from core.logger import syslog

from ...decorators import tool


@tool
def get_today_date(tool_input: Optional[Any] = None):
    """
    Get today's date.
    Reply to any question involve current date or time.
    Input is always None.
    """
    return datetime.today()


@tool
def none_of_the_above(tool_input: Optional[Any] = None):
    """
    Use this tool if none of the above tools help.
    Input is always None.
    """
    return "STOP using tools and answer user's inquiry to the best of your ability WITHOUT tools."


@tool
def get_appstore_application_info(tool_input: Any):
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
