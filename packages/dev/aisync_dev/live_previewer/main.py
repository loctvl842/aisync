import threading
from pathlib import Path

import uvicorn
from aisync.assistants.base import Assistant
from aisync.log import LogEngine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

CURRENT_FOLDER = Path(__file__).resolve().parent


class LivePreviewer:
    """Serve a server for live previewing"""

    log = LogEngine(__qualname__)
    app: FastAPI = None

    def __init__(
        self,
        assistant: Assistant,
        *,
        host: str = "localhost",
        port: int = 8402,
    ):
        self.host = host
        self.port = port
        self.assistant = assistant
        self.signaler = self.assistant.graph.signaler
        self._create_app()

    def _create_app(self):
        """Create configure Server for live previewing"""

        if self.app is not None:
            return self.app

        self.app = FastAPI()
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    async def start(self):
        """Launch server for live previewing"""

        if self.app is None:
            self._create_app()
        await self.signaler.aconnect()
        config = uvicorn.Config(
            self.app,
            port=self.port,
            host=self.host,
            log_level="error",
            reload_dirs=CURRENT_FOLDER,
        )
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        self.server_thread = thread

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.start())

    async def close(self):
        """Close the server for live previewing"""
        await self.signaler.adisconnect()
        if self.running_server:
            self.running_server.should_exit = True
            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=1.0)


def chat():
    while True:
        print("👨: ", end="", flush=True)
        user_input = input()
        if user_input == "":
            continue
        if (user_input == "\\exit") or (user_input == "\\quit"):
            break
        else:
            assistant_response = f"User said: {user_input}"
            print("🤖: ", end="", flush=True)
            print(assistant_response, "\n")


class ConsoleBot:
    def start(self):
        pass

    async def astart(self):
        pass

    def stop(self):
        pass

    async def astop(self):
        pass


if __name__ == "__main__":
    import asyncio

    from aisync.assistants import Jarvis

    assistant = Jarvis("mark_i")

    l1 = LivePreviewer(assistant)
    l1.run()
    chat()
