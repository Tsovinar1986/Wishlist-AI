"""Item schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ItemBase(BaseModel):
    title: str
    price: float | None = None
    image_url: str | None = None
    product_url: str | None = None
    allow_contributions: bool = True
    cached_snapshot_json: dict | None = None


class ItemCreate(ItemBase):
    wishlist_id: UUID


class ItemUpdate(BaseModel):
    title: str | None = None
    price: float | None = None
    image_url: str | None = None
    product_url: str | None = None
    allow_contributions: bool | None = None
    cached_snapshot_json: dict | None = None


class ItemResponse(ItemBase):
    id: UUID
    wishlist_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}
