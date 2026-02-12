"""Items router (authenticated, owner only)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.wishlist import Wishlist
from app.models.item import Item
from app.schemas.item import ItemCreate, ItemResponse, ItemUpdate
from app.services.wishlist_service import get_wishlist_by_id
from app.services.item_service import (
    create_item,
    delete_item,
    get_item_by_id,
    list_items_by_wishlist,
    update_item,
)
from app.services.product_fetch import fetch_product
from app.websocket.manager import manager

router = APIRouter(prefix="/wishlists", tags=["items"])


async def _get_own_wishlist(session: AsyncSession, wishlist_id: UUID, user: User) -> Wishlist:
    w = await get_wishlist_by_id(session, wishlist_id)
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist not found")
    if w.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your wishlist")
    return w


async def _get_own_item(
    session: AsyncSession, wishlist_id: UUID, item_id: UUID, user: User
) -> Item:
    await _get_own_wishlist(session, wishlist_id, user)
    item = await get_item_by_id(session, item_id)
    if not item or item.wishlist_id != wishlist_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router.get("/{wishlist_id}/items", response_model=list[ItemResponse])
async def list_items(
    wishlist_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    await _get_own_wishlist(session, wishlist_id, user)
    return await list_items_by_wishlist(session, wishlist_id)


def _merge_fetched_with_request(fetched, data_title, data_price, data_image_url):
    """Use fetched values when present; request body overrides (manual fallback when fetch failed)."""
    title = (fetched.title or data_title) if fetched else data_title
    price = (fetched.price if fetched and fetched.price is not None else None) or data_price
    image_url = (fetched.image_url or data_image_url) if fetched else data_image_url
    snapshot = fetched.snapshot if fetched else None
    return title, price, image_url, snapshot


@router.post("/{wishlist_id}/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item_route(
    wishlist_id: UUID,
    data: ItemCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    await _get_own_wishlist(session, wishlist_id, user)
    if data.wishlist_id != wishlist_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="wishlist_id mismatch")

    # When user submits product URL: fetch, parse OG meta; fallback to manual input if parse fails
    fetched = None
    if data.product_url:
        fetched = await fetch_product(data.product_url)
    title, price, image_url, cached_snapshot_json = _merge_fetched_with_request(
        fetched, data.title, data.price, data.image_url
    )
    if cached_snapshot_json is None and data.cached_snapshot_json is not None:
        cached_snapshot_json = data.cached_snapshot_json

    item = await create_item(
        session,
        wishlist_id=data.wishlist_id,
        title=title,
        price=price,
        image_url=image_url,
        product_url=data.product_url,
        allow_contributions=data.allow_contributions,
        cached_snapshot_json=cached_snapshot_json,
    )
    await manager.broadcast_to_wishlist(str(wishlist_id), {"type": "item_created", "item_id": str(item.id)})
    return item


@router.get("/{wishlist_id}/items/{item_id}", response_model=ItemResponse)
async def get_item(
    wishlist_id: UUID,
    item_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await _get_own_item(session, wishlist_id, item_id, user)


@router.patch("/{wishlist_id}/items/{item_id}", response_model=ItemResponse)
async def update_item_route(
    wishlist_id: UUID,
    item_id: UUID,
    data: ItemUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    item = await _get_own_item(session, wishlist_id, item_id, user)
    kwargs = data.model_dump(exclude_unset=True)

    # If product_url is being set/updated, refetch and cache snapshot
    if "product_url" in kwargs and kwargs["product_url"]:
        fetched = await fetch_product(kwargs["product_url"])
        if fetched:
            kwargs.setdefault("title", fetched.title or item.title)
            if fetched.price is not None:
                kwargs.setdefault("price", fetched.price)
            if fetched.image_url:
                kwargs.setdefault("image_url", fetched.image_url)
            kwargs["cached_snapshot_json"] = fetched.snapshot
    elif "product_url" in kwargs and not kwargs["product_url"]:
        kwargs["cached_snapshot_json"] = None

    await update_item(session, item, **kwargs)
    await manager.broadcast_to_wishlist(str(wishlist_id), {"type": "item_updated", "item_id": str(item_id)})
    return item


@router.delete("/{wishlist_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item_route(
    wishlist_id: UUID,
    item_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    item = await _get_own_item(session, wishlist_id, item_id, user)
    await delete_item(session, item)
    await manager.broadcast_to_wishlist(str(wishlist_id), {"type": "item_deleted", "item_id": str(item_id)})
