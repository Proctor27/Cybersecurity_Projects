"""
AngelaMos | 2026
manager.py

Fan-out broadcaster for operator WebSocket connections with role-based tracking

OpsManager keeps a dictionary of active operator WebSocket connections mapped to their roles.
connect accepts a new connection with an assigned role; broadcast serializes an event dict
as JSON and sends it to all connected operators regardless of role, silently dropping
any connections that fail to send.

Connects to:
beacon/router.py - broadcast called for beacon connect/disconnect/result
ops/router.py - connect, disconnect, get_role, and broadcast called per operator
main.py - creates singleton on startup
"""

import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class OpsManager:
    """
    Manages operator WebSocket connections with roles and broadcasts C2 events
    """

    def __init__(self) -> None:
        """
        Initialize empty operator connection dictionary
        """
        self._connections: dict[WebSocket, str] = {}

    async def connect(self, ws: WebSocket, role: str = "admin") -> None:
        """
        Accept and track a new operator WebSocket connection with a specified role
        """
        self._connections[ws] = role
        logger.info("Operator connected (%s) (%d total)", role, len(self._connections))

    def disconnect(self, ws: WebSocket) -> None:
        """
        Remove an operator WebSocket connection
        """
        if ws in self._connections:
            del self._connections[ws]
            logger.info("Operator disconnected (%d remaining)", len(self._connections))

    def get_role(self, ws: WebSocket) -> str:
        """
        Retrieve the role assigned to a connected operator
        """
        return self._connections.get(ws, "viewer")

    async def broadcast(self, event: dict[str, Any]) -> None:
        """
        Send an event to all connected operators regardless of role, removing stale connections
        """
        stale: list[WebSocket] = []
        payload = json.dumps(event)

        for ws in list(self._connections.keys()):
            try:
                await ws.send_text(payload)
            except (ConnectionError, RuntimeError):
                stale.append(ws)

        for ws in stale:
            self.disconnect(ws)

    @property
    def connection_count(self) -> int:
        """
        Number of active operator connections
        """
        return len(self._connections)