from fastapi import APIRouter

from aisync_api.routes.main.ping import router as ping_router
from aisync_api.routes.main.auth import router as auth_router

router = APIRouter()
router.include_router(ping_router)
router.include_router(auth_router)

__all__ = ["router"]
