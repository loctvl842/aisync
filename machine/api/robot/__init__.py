from fastapi import APIRouter

from .llm import router as llm_router
from .embedder import router as embedder_router

router = APIRouter(prefix="/robot")
router.include_router(llm_router)
router.include_router(embedder_router)

__all__ = ["router"]
