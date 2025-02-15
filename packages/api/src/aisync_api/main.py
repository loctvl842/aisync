from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from aisync_api.env import env
from aisync_api.routes import main, tool
from aisync_api.server.config import AppConfigurer
from aisync_api.server.constants import SUITS_DIR


@asynccontextmanager
async def main_lifespan(app: FastAPI):
    yield


async def tool_lifespan(app: FastAPI):
    yield


def setup_applications() -> list[FastAPI]:
    """Create and configure all applications.

    Returns:
        List[FastAPI]: List of configured applications
    """
    main_app = FastAPI(
        title="AISync API",
        description="AISync API",
        version="0.0.1",
        root_path="/api",
        docs_url=None,
        redoc_url=None,
        lifespan=main_lifespan,
    )
    main_app.include_router(main.router)

    tool_app = FastAPI(
        title="AISync Tools",
        description="AISync Tools",
        version="0.0.1",
        root_path=f"{main_app.root_path}/tools",
        docs_url=None,
        redoc_url=None,
    )
    tool_app.include_router(tool.router)

    main_app.mount("/tools", tool_app)

    # Configure all apps
    applications = [main_app, tool_app]
    for app in applications:
        configurer = AppConfigurer(app)
        configurer.setup_all()

    return applications


applications = setup_applications()
server = applications[0]

if __name__ == "__main__":
    uvicorn.run(
        "aisync_api.main:server",
        host=env.API_HOST,
        port=env.API_PORT,
        reload=env.API_DEBUG,
        reload_excludes=[SUITS_DIR],
    )
