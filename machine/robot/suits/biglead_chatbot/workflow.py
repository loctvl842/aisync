from core.logger import syslog

from ...aisync import workflow


@workflow
def chatbot_workflow(**kwargs):
    assistant = kwargs["assistant"]

    # set start point
    assistant.compiler.set_start_point("monitor")
    syslog.info("Setting start point")
