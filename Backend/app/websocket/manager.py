"""WebSocket connection manager for real-time broadcasting."""

import json
from collections import defaultdict
from datetime import datetime
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    """Manage WebSocket connections per wishlist for real-time updates.
    Maintains active connections per wishlist and broadcasts events without exposing user identity.
    """

    def __init__(self) -> None:
        # wishlist_id -> set of WebSocket
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, websocket: WebSocket, wishlist_id: str) -> None:
        await websocket.accept()
        self._connections[wishlist_id].add(websocket)

    def disconnect(self, websocket: WebSocket, wishlist_id: str) -> None:
        self._connections[wishlist_id].discard(websocket)
        if not self._connections[wishlist_id]:
            del self._connections[wishlist_id]

    def active_connections_count(self, wishlist_id: str) -> int:
        return len(self._connections.get(wishlist_id, set()))

    async def broadcast_to_wishlist(
        self, wishlist_id: str, message: dict[str, Any]
    ) -> None:
        """Send message to all clients subscribed to this wishlist."""
        payload = json.dumps(message)
        dead = set()
        for ws in self._connections.get(wishlist_id, set()):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self._connections[wishlist_id].discard(ws)

    @staticmethod
    def build_item_state_event(
        event_type: str,
        item_id: str,
        reserved_total: float,
        reservations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Build event payload with updated item state. No user_id or guest_name."""
        out = []
        for r in reservations:
            created_at = r.get("created_at")
            if isinstance(created_at, datetime):
                created_at = created_at.isoformat()
            out.append({
                "id": r.get("id"),
                "amount": r.get("amount"),
                "is_full_reservation": r.get("is_full_reservation", False),
                "created_at": created_at,
            })
        return {
            "type": event_type,
            "item_id": item_id,
            "reserved_total": reserved_total,
            "reservations": out,
        }


# Singleton used by routes
manager = ConnectionManager()
