from fastapi import APIRouter

from aisync_api.routes.ping import router as ping_router
from aisync_api.routes.v1 import router as router_v1

router = APIRouter()
router.include_router(ping_router)
router.include_router(router_v1)

__all__ = ["router"]
