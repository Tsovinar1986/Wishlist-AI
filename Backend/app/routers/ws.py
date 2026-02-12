"""WebSocket endpoint: subscribe to wishlist updates (real-time)."""

from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.websocket.manager import manager

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/wishlist/{wishlist_id}")
async def websocket_wishlist(websocket: WebSocket, wishlist_id: UUID):
    """Subscribe to real-time updates for a wishlist (items, reservations).
    Events: item_reserved, contribution_added (updated item state, no user identity).
    """
    key = str(wishlist_id)
    await manager.connect(websocket, key)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, key)
