"""Wishlists router (authenticated). Public by slug is in public router."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.wishlist import Wishlist
from app.schemas.wishlist import WishlistCreate, WishlistResponse, WishlistUpdate
from app.services.wishlist_service import (
    create_wishlist as svc_create,
    delete_wishlist,
    get_wishlist_by_id,
    list_wishlists_by_owner,
    update_wishlist as svc_update,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/wishlists", tags=["wishlists"])


async def _get_own_wishlist(session: AsyncSession, wishlist_id: UUID, user: User) -> Wishlist:
    w = await get_wishlist_by_id(session, wishlist_id)
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist not found")
    if w.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your wishlist")
    return w


@router.get("", response_model=list[WishlistResponse])
async def list_my_wishlists(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await list_wishlists_by_owner(session, user.id)


@router.post("", response_model=WishlistResponse, status_code=status.HTTP_201_CREATED)
async def create_wishlist(
    data: WishlistCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    w = await svc_create(
        session, user.id, data.title, data.description, data.deadline
    )
    return w


@router.get("/{wishlist_id}", response_model=WishlistResponse)
async def get_wishlist(
    wishlist_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    w = await _get_own_wishlist(session, wishlist_id, user)
    return w


@router.patch("/{wishlist_id}", response_model=WishlistResponse)
async def update_wishlist(
    wishlist_id: UUID,
    data: WishlistUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    w = await _get_own_wishlist(session, wishlist_id, user)
    kwargs = data.model_dump(exclude_unset=True)
    await svc_update(session, w, **kwargs)
    return w


@router.delete("/{wishlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_wishlist(
    wishlist_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    w = await _get_own_wishlist(session, wishlist_id, user)
    await delete_wishlist(session, w)
