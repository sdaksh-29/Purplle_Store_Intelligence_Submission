from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json
from typing import List
from app.core.bus import event_bus
from app.schemas.event import StoreEvent

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

# Background task to listen to Event Bus and Broadcast
async def broadcast_event(event: StoreEvent):
    event_data = event.model_dump()
    event_data["timestamp"] = event_data["timestamp"].isoformat()
    event_data["event_id"] = str(event_data["event_id"])
    await manager.broadcast(json.dumps(event_data))

# This needs to be hooked up in main.py
def setup_ws_broadcaster():
    asyncio.create_task(event_bus.subscribe("store_events", broadcast_event))

@router.websocket("/live")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # We don't expect messages from client, just keep connection open
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
