from core.utils.decorators import stopwatch
from machine.robot.aisync.engines.llm import get_llm_cls, get_llm_object, list_supported_llm_models

@stopwatch()
def test():
    print(list_supported_llm_models())

test()
