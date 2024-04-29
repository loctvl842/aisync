import traceback

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.logger import syslog
from machine.robot.assistants import Jarvis
from machine.robot.assistants.base import Assistant

router = APIRouter()


async def receive_message(websocket: WebSocket, assistant: Assistant):
    while True:
        user_input = await websocket.receive_text()
        assistant_response = assistant.respond(user_input)
        await websocket.send_text(f"Message text was: {assistant_response}")


@router.websocket("/ws")
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str = "user"):
    assistants = websocket.app.state.assistants

    if user_id in assistants.keys():
        assistant = assistants[user_id]
    else:
        assistant = Jarvis()
        assistants[user_id] = assistant

    await websocket.accept()
    try:
        await receive_message(websocket, assistant)
    except WebSocketDisconnect:
        syslog.info("WebSocket connection closed")
    except Exception as e:
        syslog.error(f"WebSocket error: {e}")
        traceback.print_exc()
