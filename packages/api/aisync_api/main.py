import asyncio
import traceback
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from watchfiles import awatch
from websockets import connect

from aisync_api.env import env
from aisync_api.routes import main, tool
from aisync_api.server.config import AppConfigurer
from aisync_api.server.constants import SUITS_DIR
from aisync_api.server.log import log


@asynccontextmanager
async def main_lifespan(app: FastAPI):
    yield


async def tool_lifespan(app: FastAPI):
    async def awatching(stop_event: asyncio.Event):
        log.info(f"Starting watcher on directory: {SUITS_DIR}")
        try:
            async for changes in awatch(SUITS_DIR):
                if stop_event.is_set():
                    break
                log.info(f"Changes detected: {changes}")
            async with connect("ws://localhost:8080/api/v1/ws") as ws:
                    await ws.send("reload:suits")
        except asyncio.CancelledError:
            log.info("Watcher task cancelled.")
        except Exception as e:
            log.error(f"Error in watcher task: {e}")
            traceback.print_exc()
        finally:
            log.info("Asynchronous watcher has been stopped.")

    stop_event = asyncio.Event()
    watcher_task = asyncio.create_task(awatching(stop_event))

    yield

    stop_event.set()
    watcher_task.cancel()

    try:
        await watcher_task
    except asyncio.CancelledError:
        log.info("Watcher task successfully cancelled.")
    except Exception as e:
        log.error(f"Error while cancelling watcher task: {e}")


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
