"""Pusher Channels auth endpoint for private and presence channel subscriptions (FastAPI)."""

import hashlib
import hmac
import logging

from fastapi import APIRouter, Depends, Form, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_current_user_optional
from app.core.config import get_settings
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pusher", tags=["pusher"])


class PusherAuthResponse(BaseModel):
    """Response for POST /api/pusher/auth — auth string for Pusher JS."""

    auth: str


class PusherPresenceAuthResponse(PusherAuthResponse):
    """Response for presence channel — includes channel_data."""

    channel_data: str


def _sign_pusher(string_to_sign: str, secret: str) -> str:
    """HMAC SHA256 hex digest of string_to_sign using secret."""
    return hmac.new(
        secret.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


@router.post(
    "/auth",
    response_model=PusherAuthResponse,
    summary="Pusher channel auth",
    description="Authorize a Pusher private or presence channel subscription. Send form body: socket_id, channel_name, optional channel_data (presence). For private-* and presence-* channels send Authorization: Bearer <JWT>.",
    responses={
        200: {"description": "Auth string for Pusher JS"},
        401: {"description": "Authentication required for private/presence channel"},
        503: {"description": "Pusher not configured"},
    },
)
async def pusher_auth(
    socket_id: str = Form(..., min_length=1, description="Pusher socket_id"),
    channel_name: str = Form(..., min_length=1, description="Channel name (e.g. private-wishlist-123)"),
    channel_data: str | None = Form(None, description="JSON string for presence channel_data"),
    user: User | None = Depends(get_current_user_optional),
) -> PusherAuthResponse | PusherPresenceAuthResponse:
    settings = get_settings()
    if not settings.pusher_key or not settings.pusher_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pusher is not configured",
        )

    channel_name = channel_name.strip()
    socket_id = socket_id.strip()

    is_private = channel_name.startswith("private-")
    is_presence = channel_name.startswith("presence-")

    if is_private or is_presence:
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required for private/presence channels",
            )
        # Optional: restrict channel access by name (e.g. private-wishlist-<id> only for owner)
        # if channel_name.startswith("private-wishlist-") or channel_name.startswith("presence-wishlist-"):
        #     wishlist_id = channel_name.split("-")[-1]
        #     if not await user_can_subscribe_to_wishlist(user, wishlist_id):
        #         raise HTTPException(403, "Not allowed to subscribe to this channel")

    try:
        if is_presence and channel_data and channel_data.strip():
            # Presence: sign socket_id:channel_name:channel_data (channel_data is JSON string as sent by client)
            string_to_sign = f"{socket_id}:{channel_name}:{channel_data}"
            signature = _sign_pusher(string_to_sign, settings.pusher_secret)
            return PusherPresenceAuthResponse(
                auth=f"{settings.pusher_key}:{signature}",
                channel_data=channel_data,
            )
        else:
            # Private channel (or presence without channel_data - client should send it)
            string_to_sign = f"{socket_id}:{channel_name}"
            signature = _sign_pusher(string_to_sign, settings.pusher_secret)
            return PusherAuthResponse(auth=f"{settings.pusher_key}:{signature}")
    except Exception as e:
        logger.warning("Pusher auth failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to authorize channel",
        )
