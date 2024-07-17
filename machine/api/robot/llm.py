from fastapi import APIRouter

from machine.robot.aisync.engines.llm import get_llm_schemas

router = APIRouter(prefix="/llms", tags=["llms"])


@router.get("")
async def get_llms():
    return get_llm_schemas()
