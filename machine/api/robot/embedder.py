from fastapi import APIRouter

from machine.robot.aisync.engines.embedder import get_embedder_schemas

router = APIRouter(prefix="/embedders", tags=["embedders"])


@router.get("")
async def get_embedders():
    return get_embedder_schemas()
