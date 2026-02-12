"""Wishlist service (async). Slug generation, public by slug."""

import secrets
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.wishlist import Wishlist


def _generate_slug() -> str:
    return secrets.token_urlsafe(12)


async def get_wishlist_by_id(
    session: AsyncSession, wishlist_id: UUID, *, load_items: bool = False
) -> Wishlist | None:
    q = select(Wishlist).where(Wishlist.id == wishlist_id)
    if load_items:
        q = q.options(selectinload(Wishlist.items))
    result = await session.execute(q)
    return result.scalar_one_or_none()


async def get_wishlist_by_slug(
    session: AsyncSession, slug: str, *, load_items: bool = True
) -> Wishlist | None:
    q = select(Wishlist).where(Wishlist.public_slug == slug)
    if load_items:
        q = q.options(selectinload(Wishlist.items))
    result = await session.execute(q)
    return result.scalar_one_or_none()


async def list_wishlists_by_owner(
    session: AsyncSession, owner_id: UUID
) -> list[Wishlist]:
    result = await session.execute(
        select(Wishlist).where(Wishlist.owner_id == owner_id).order_by(Wishlist.created_at.desc())
    )
    return list(result.scalars().all())


async def create_wishlist(
    session: AsyncSession, owner_id: UUID, title: str, description: str | None = None, deadline=None
) -> Wishlist:
    slug = _generate_slug()
    wishlist = Wishlist(
        owner_id=owner_id,
        title=title,
        description=description,
        public_slug=slug,
        deadline=deadline,
    )
    session.add(wishlist)
    await session.flush()
    await session.refresh(wishlist)
    return wishlist


async def update_wishlist(
    session: AsyncSession, wishlist: Wishlist, **kwargs
) -> Wishlist:
    for k, v in kwargs.items():
        if hasattr(wishlist, k):
            setattr(wishlist, k, v)
    await session.flush()
    await session.refresh(wishlist)
    return wishlist


async def delete_wishlist(session: AsyncSession, wishlist: Wishlist) -> None:
    await session.delete(wishlist)
    await session.flush()
