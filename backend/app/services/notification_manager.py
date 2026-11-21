
import asyncio
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class NotificationConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()

        async with self._lock:
            self.active_connections.setdefault(
                user_id,
                set(),
            ).add(websocket)

        logger.info("User %s connected to notifications.", user_id)

    async def disconnect(self, user_id: int, websocket: WebSocket):
        async with self._lock:
            connections = self.active_connections.get(user_id)

            if connections:
                connections.discard(websocket)

                if not connections:
                    self.active_connections.pop(user_id, None)

        logger.info("User %s disconnected from notifications.", user_id)

    async def send_to_user(
        self,
        user_id: int,
        notification: dict,
    ):
        async with self._lock:
            connections = list(
                self.active_connections.get(user_id, set())
            )

        disconnected = []

        for websocket in connections:
            try:
                await websocket.send_json(notification)
            except Exception:
                logger.warning(
                    "Could not deliver notification to user %s.",
                    user_id,
                )
                disconnected.append(websocket)

        for websocket in disconnected:
            await self.disconnect(user_id, websocket)


notification_manager = NotificationConnectionManager()
