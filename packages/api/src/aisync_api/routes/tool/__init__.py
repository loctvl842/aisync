from fastapi import APIRouter

from aisync_api.routes.tool.ping import router as ping_router

router = APIRouter()
router.include_router(ping_router)

__all__ = ["router"]
