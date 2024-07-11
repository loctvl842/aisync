from ...decorators import workflow
from core.logger import syslog

@workflow
def chatbot_workflow(**kwargs):
    assistant = kwargs["assistant"]
    
    # set start point
    assistant.compiler.set_start_point("intent_manager")
    syslog.info("Setting start point")
    
    # set end point
    # assistant.compiler.set_end_point("END")    
    # syslog.info("Setting end point")
    
    # set the graph
    # assistant.compiler.add_edge("intent_manager", "low_code_agent")

