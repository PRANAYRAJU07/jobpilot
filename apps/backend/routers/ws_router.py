import asyncio
import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List

router = APIRouter(tags=["websockets"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        stale = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                stale.append(connection)
        for s in stale:
            self.disconnect(s)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    pubsub = None
    try:
        import redis.asyncio as aioredis
        r = aioredis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, db=0, decode_responses=True)
        pubsub = r.pubsub()
        await pubsub.psubscribe("global_events", "user_events:*")

        async def _reader():
            async for message in pubsub.listen():
                if message and message.get("type") in ("message", "pmessage"):
                    data = message.get("data")
                    if isinstance(data, str):
                        await websocket.send_text(data)

        reader_task = asyncio.create_task(_reader())
        try:
            while True:
                await websocket.receive_text()
        finally:
            reader_task.cancel()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        # Fallback loop if Redis pubsub is unreachable
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(websocket)
    finally:
        if pubsub:
            try:
                await pubsub.close()
            except Exception:
                pass
        manager.disconnect(websocket)
