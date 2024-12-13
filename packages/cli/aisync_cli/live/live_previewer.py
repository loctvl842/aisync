import asyncio
import threading
import traceback
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Set

import uvicorn
from aisync.assistants.base import Assistant
from aisync.notification.in_memory import (
    InMemoryNotification,
    NotificationChannel,
    NotificationMessage,
)
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from aisync_cli.live.watcher import FileWatcher
from aisync_cli.live.watcher.file_watcher import ChangeInfo
from aisync_cli.log import LogEngine

CURRENT_FOLDER = Path(__file__).resolve().parent


class LivePreviewer:
    """Serve FastAPI app for live previewing"""

    def __init__(
        self,
        *,
        host: str = "localhost",
        port: int = 8402,
        assistant: Assistant,
        suit: str,
    ):
        self.host = host
        self.port = port
        self.assistant = assistant
        self.suit = suit
        self.app = self._create_app()
        self.log = LogEngine(self.__class__.__name__)
        self.should_exit = threading.Event()
        self.notification_hub = InMemoryNotification()
        self.server_thread = None
        self.running_server = None

    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.FILE_CHANGED

    def _create_app(self):
        """Create and configure lifespan for FastAPI"""

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            self.background_tasks: Set[asyncio.Task] = set()

            async def callback(change_info: ChangeInfo):
                try:
                    print('caicalon', self.channel.value)
                    # async with websockets.connect(
                    #     # f"ws://{self.host}/{self.port}/ws/{self.channel.value}/publish"
                    #     f"ws://localhost:8402/ws/{self.channel.value}/publish"
                    # ) as wst:
                    #     await wst.send("reload")
                    await self.notification_hub.publish(
                        channel=self.channel,
                        message=NotificationMessage(
                            id=f"{uuid.uuid4()}",
                            channel=self.channel,
                            content="reload",
                            timestamp=datetime.now(),
                        ),
                    )
                except Exception as e:
                    self.log.error(f"Error while reloading: {e}")
                    traceback.print_exc()
                    return False

            file_watcher = FileWatcher(
                watch_path=self.assistant.suit.path,
                callback=callback,
            )
            watcher_task = asyncio.create_task(file_watcher.start_watching())
            self.background_tasks.add(watcher_task)

            try:
                yield
            finally:
                await file_watcher.stop()
                for task in self.background_tasks:
                    if not task.done():
                        task.cancel()
                        try:
                            await task  # Await cancelled tasks
                        except asyncio.CancelledError:
                            pass
                if self.background_tasks:
                    try:
                        await asyncio.wait_for(
                            asyncio.gather(*self.background_tasks, return_exceptions=True),
                            timeout=5.0,
                        )
                        self.log.info("All background tasks completed")
                    except asyncio.TimeoutError:
                        self.log.warning("Some background tasks took too long to complete")
                    except Exception as e:
                        self.log.error(f"Error during task shutting down: {e}")

                self.should_exit.set()

        app = FastAPI(lifespan=lifespan)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        return app

    def _init_routes(
        self,
    ):
        if not self.app:
            raise ValueError("App not initialized.")

        templates = Jinja2Templates(directory=CURRENT_FOLDER / "templates")
        self.app.mount(
            "/static", StaticFiles(directory=CURRENT_FOLDER / "static"), name="static"
        )

        @self.app.get("/")
        async def root(request: Request):
            self.assistant.suit.activate()
            graph = list(self.assistant.suit.graphs.values())[0]
            context = {
                "code": graph.to_mermaid(),
                "subscribe_url": f"ws://{self.host}:{self.port}/ws/{self.channel.value}/subscribe",
                "suit": self.suit,
                "root_path": self.app.root_path,
            }
            response = templates.TemplateResponse(
                "index.html", {"request": request, **context}
            )
            return response

        @self.app.get("/graph")
        async def get_graph_mermaid():
            self.assistant.suit.activate()
            graph = list(self.assistant.suit.graphs.values())[0]
            return {"code": graph.to_mermaid()}

        @self.app.websocket("/ws/{channel}/subscribe")
        async def subscribe(websocket: WebSocket, channel: str):
            await websocket.accept()

            async def callback(notification: NotificationMessage):
                try:
                    await websocket.send_json(
                        {
                            "id": notification.id,
                            "channel": notification.channel,
                            "timestamp": notification.timestamp.isoformat(),
                            "metadata": notification.metadata,
                        }
                    )
                except Exception as e:
                    self.log.error(f"Error while sending message: {e}")
                    return False
                return True

            await self.notification_hub.subscribe(
                    channel=self.channel, callback=callback
                    )
            try:
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                await self.notification_hub.unsubscribe(callback=callback)

        @self.app.websocket("/ws/{channel}/publish")
        async def publish(websocket: WebSocket, channel: str):
            await websocket.accept()

            try:
                while True:
                    action = await websocket.receive_text()
                    if action == "reload":
                        # Then broadcast to other websockets
                        await self.notification_hub.publish(
                            channel=self.channel,
                            message=NotificationMessage(
                                id=f"{id(websocket)}",
                                channel=self.channel,
                                content=action,
                                timestamp=datetime.now(),
                            ),
                        )
            except WebSocketDisconnect:
                pass

    async def run_server(self):
        """Launch FastAPI server for live previewing in a separate thread"""

        await self.notification_hub.connect()
        self._init_routes()
        config = uvicorn.Config(
            self.app,
            port=self.port,
            host=self.host,
            log_level="error",
            reload_dirs=[CURRENT_FOLDER],
        )
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        self.log.info(
            f" Live preview suit {self.suit} at http://{self.host}:{self.port}"
        )
        self.running_server = server
        self.server_thread = thread

    async def shutdown(self):
        await self.notification_hub.disconnect()
        if self.running_server:
            self.running_server.should_exit = True
            self.should_exit.set()
            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=1.0)
