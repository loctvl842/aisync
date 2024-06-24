from datetime import datetime
from typing import Any, Optional

from langchain.agents import tool

from core.logger import syslog


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

@tool
def workflow_automation_price_estimation(tool_input: int):
    """
    Estimate the price of a workflow automation setup
    Reply with a full estimated quote for the user's requested workflow automation setup
    Input is a description of the workflow automation setup in the form of a dictionary.
    The input should be an integer indicating the number of connections needed to setup the workflow automation.
    """
    return f"\n- Cost: ${tool_input * 100}\n- Maintenance fee: $50 / year\n"

@tool
def low_code_price_estimation(tool_input: dict):
    """
    Estimate the price of a low-code application.
    Reply with a full estimated quote for the user's requested low-code application
    Input is a description of the application in the form of a dictionary.
    The input format should be as follows:
    {
        "platform": One of the values "wix", "shopify", "wordpress",
        "num_of_plugins": number of plugins users want to include,
        "template_price": template price of the user's choice
    }
    """

    for key in ["platform", "num_of_plugins", "template_price"]:
        if key not in tool_input:
            return f"Missing key: {key} in the input dictionary"
    
    platform = (tool_input["platform"]).lower()
    price_by_platform = {
        "wix": 700,
        "shopify": 800,
        "wordpress": 600
    }
    if platform not in price_by_platform.keys():
        return "Unsupported platform by Rockship"
    platform_cost = price_by_platform[platform]
    maintenance_fee = 100
    plugin_fee = tool_input["num_of_plugins"] * 50
    price_report = f'\n- Platform cost: ${platform_cost}\n'
    price_report += f'- Maintenance fee: ${maintenance_fee} / year\n'
    price_report += f'- Plugin cost: ${plugin_fee}\n'
    price_report += f'- Template cost: ${tool_input["template_price"]}\n'
    price_report += f'- Total cost: ${platform_cost + plugin_fee + tool_input["template_price"]}\n\n'
    return price_report
