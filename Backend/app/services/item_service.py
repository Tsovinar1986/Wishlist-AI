"""Item service (async)."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.item import Item


async def get_item_by_id(
    session: AsyncSession, item_id: UUID, *, load_reservations: bool = False
) -> Item | None:
    q = select(Item).where(Item.id == item_id)
    if load_reservations:
        q = q.options(selectinload(Item.reservations))
    result = await session.execute(q)
    return result.scalar_one_or_none()


async def list_items_by_wishlist(session: AsyncSession, wishlist_id: UUID) -> list[Item]:
    result = await session.execute(
        select(Item).where(Item.wishlist_id == wishlist_id).order_by(Item.created_at)
    )
    return list(result.scalars().all())


async def create_item(
    session: AsyncSession,
    wishlist_id: UUID,
    title: str,
    price: float | None = None,
    image_url: str | None = None,
    product_url: str | None = None,
    allow_contributions: bool = True,
    cached_snapshot_json: dict | None = None,
) -> Item:
    item = Item(
        wishlist_id=wishlist_id,
        title=title,
        price=price,
        image_url=image_url,
        product_url=product_url,
        allow_contributions=allow_contributions,
        cached_snapshot_json=cached_snapshot_json,
    )
    session.add(item)
    await session.flush()
    await session.refresh(item)
    return item


async def update_item(session: AsyncSession, item: Item, **kwargs) -> Item:
    for k, v in kwargs.items():
        if hasattr(item, k):
            setattr(item, k, v)
    await session.flush()
    await session.refresh(item)
    return item


async def delete_item(session: AsyncSession, item: Item) -> None:
    await session.delete(item)
    await session.flush()
