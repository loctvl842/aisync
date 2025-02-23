from fastapi import APIRouter

from aisync_api.routes.main.system import router as system_router
from aisync_api.routes.main.ping import router as ping_router
from aisync_api.routes.main.auth import router as auth_router
from aisync_api.routes.main.project import router as project_router
from aisync_api.routes.main.team import router as team_router

router = APIRouter()
router.include_router(system_router)
router.include_router(ping_router)
router.include_router(auth_router)
router.include_router(project_router)
router.include_router(team_router)

__all__ = ["router"]
