"""Public routes: wishlist by slug (no login required)."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.wishlist import WishlistPublicResponse
from app.schemas.item import ItemResponse
from app.schemas.reservation import ReservationResponseForOwner
from app.services.wishlist_service import get_wishlist_by_slug
from app.services.reservation_service import list_reservations_for_item, total_reserved_for_item
from pydantic import BaseModel

router = APIRouter(prefix="/public", tags=["public"])


class ItemWithReservations(BaseModel):
    id: UUID
    wishlist_id: UUID
    title: str
    price: float | None
    image_url: str | None
    product_url: str | None
    allow_contributions: bool
    cached_snapshot_json: dict | None
    created_at: datetime
    reserved_total: float
    reservations: list[ReservationResponseForOwner]


class PublicWishlistResponse(BaseModel):
    id: UUID
    owner_id: UUID
    title: str
    description: str | None
    public_slug: str
    deadline: datetime | None
    created_at: datetime
    items: list[ItemWithReservations]


@router.get("/wishlists/by-slug/{slug}", response_model=PublicWishlistResponse)
async def get_wishlist_by_slug_public(
    slug: str,
    session: AsyncSession = Depends(get_db),
):
    w = await get_wishlist_by_slug(session, slug, load_items=True)
    if not w:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist not found",
        )
    items_out = []
    for item in w.items:
        total = await total_reserved_for_item(session, item.id)
        res_list = await list_reservations_for_item(session, item.id)
        items_out.append(
            ItemWithReservations(
                id=item.id,
                wishlist_id=item.wishlist_id,
                title=item.title,
                price=float(item.price) if item.price is not None else None,
                image_url=item.image_url,
                product_url=item.product_url,
                allow_contributions=item.allow_contributions,
                cached_snapshot_json=item.cached_snapshot_json,
                created_at=item.created_at,
                reserved_total=float(total),
                reservations=[
                    ReservationResponseForOwner(
                        id=r.id,
                        item_id=r.item_id,
                        amount=float(r.amount),
                        is_full_reservation=r.is_full_reservation,
                        created_at=r.created_at,
                    )
                    for r in res_list
                ],
            )
        )
    return PublicWishlistResponse(
        id=w.id,
        owner_id=w.owner_id,
        title=w.title,
        description=w.description,
        public_slug=w.public_slug,
        deadline=w.deadline,
        created_at=w.created_at,
        items=items_out,
    )
