"""Reservations router. Owner must NOT see reservation identities.
Transaction-safe reservation logic; WebSocket broadcast after commit (item_reserved / contribution_added).
"""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_user_optional
from app.db.session import get_db
from app.models.user import User
from app.models.wishlist import Wishlist
from app.models.reservation import Reservation
from app.schemas.reservation import (
    ReservationCreate,
    ReservationResponse,
    ReservationResponseForOwner,
    ReservationResponseForGuest,
)
from app.services.wishlist_service import get_wishlist_by_id
from app.services.item_service import get_item_by_id
from app.services.reservation_service import (
    create_reservation as svc_create_reservation,
    list_reservations_for_item,
    total_reserved_for_item,
)
from app.websocket.manager import manager

router = APIRouter(prefix="/wishlists", tags=["reservations"])


async def _get_wishlist_and_item(
    session: AsyncSession, wishlist_id: UUID, item_id: UUID
) -> tuple[Wishlist | None, object]:
    w = await get_wishlist_by_id(session, wishlist_id)
    if not w:
        return None, None
    item = await get_item_by_id(session, item_id)
    if not item or item.wishlist_id != wishlist_id:
        return w, None
    return w, item


def _reservation_for_owner(r: Reservation) -> ReservationResponseForOwner:
    """Strip user_id and guest_name for owner."""
    return ReservationResponseForOwner(
        id=r.id,
        item_id=r.item_id,
        amount=float(r.amount),
        is_full_reservation=r.is_full_reservation,
        created_at=r.created_at,
    )


def _reservation_for_guest(r: Reservation) -> ReservationResponseForGuest:
    return ReservationResponseForGuest(
        id=r.id,
        item_id=r.item_id,
        amount=float(r.amount),
        is_full_reservation=r.is_full_reservation,
        guest_name=r.guest_name,
        created_at=r.created_at,
    )


def _anonymized_reservations_for_broadcast(reservations: list[Reservation]) -> list[dict]:
    """Item state for WebSocket: no user_id, no guest_name."""
    return [
        {
            "id": str(r.id),
            "amount": float(r.amount),
            "is_full_reservation": r.is_full_reservation,
            "created_at": r.created_at,
        }
        for r in reservations
    ]


@router.post(
    "/{wishlist_id}/items/{item_id}/reservations",
    response_model=ReservationResponseForGuest,
    status_code=status.HTTP_201_CREATED,
)
async def create_reservation(
    wishlist_id: UUID,
    item_id: UUID,
    data: ReservationCreate,
    background_tasks: BackgroundTasks,
    user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_db),
):
    """Create reservation (logged-in or guest). Transaction-safe: single DB transaction prevents double reserve.
    Broadcasts item_reserved or contribution_added after commit, with updated item state (no user identity).
    """
    w, item = await _get_wishlist_and_item(session, wishlist_id, item_id)
    if not w or not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist or item not found")
    if not item.allow_contributions and not data.is_full_reservation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item does not allow partial contributions",
        )
    try:
        reservation = await svc_create_reservation(
            session,
            item_id=item_id,
            amount=data.amount,
            is_full_reservation=data.is_full_reservation,
            user_id=user.id if user else None,
            guest_name=data.guest_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    # Build payload from current session state (includes new reservation); broadcast after response (after commit)
    total = await total_reserved_for_item(session, item_id)
    reservations = await list_reservations_for_item(session, item_id)
    event_type = "item_reserved" if data.is_full_reservation else "contribution_added"
    payload = manager.build_item_state_event(
        event_type=event_type,
        item_id=str(item_id),
        reserved_total=float(total),
        reservations=_anonymized_reservations_for_broadcast(reservations),
    )
    background_tasks.add_task(
        manager.broadcast_to_wishlist,
        str(wishlist_id),
        payload,
    )
    return _reservation_for_guest(reservation)


@router.get(
    "/{wishlist_id}/items/{item_id}/reservations",
    response_model=list[ReservationResponse],
)
async def list_reservations(
    wishlist_id: UUID,
    item_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """List reservations. Owner gets anonymized list (no user_id, no guest_name)."""
    w, item = await _get_wishlist_and_item(session, wishlist_id, item_id)
    if not w or not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist or item not found")
    if w.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your wishlist")
    reservations = await list_reservations_for_item(session, item_id)
    return [_reservation_for_owner(r) for r in reservations]
