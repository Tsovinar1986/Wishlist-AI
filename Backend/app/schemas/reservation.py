"""Reservation schemas. Owner must NOT see user/guest identity."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ReservationBase(BaseModel):
    amount: float = Field(..., ge=0)
    is_full_reservation: bool = False
    guest_name: str | None = None


class ReservationCreate(ReservationBase):
    item_id: UUID


class ReservationResponse(BaseModel):
    """For item detail: amount and type only (no identity)."""

    id: UUID
    item_id: UUID
    amount: float
    is_full_reservation: bool
    created_at: datetime
    # Never expose user_id or guest_name to wishlist owner

    model_config = {"from_attributes": True}


class ReservationResponseForOwner(ReservationResponse):
    """Owner view: no user_id, no guest_name (privacy)."""

    pass


class ReservationResponseForGuest(BaseModel):
    """When the requester is the reserver or public: can show own guest_name."""

    id: UUID
    item_id: UUID
    amount: float
    is_full_reservation: bool
    guest_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
