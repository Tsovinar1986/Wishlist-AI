"""Reservation service: transactions to prevent double reservation, no identity to owner."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item import Item
from app.models.reservation import Reservation


async def get_reservation_by_id(session: AsyncSession, reservation_id: UUID) -> Reservation | None:
    result = await session.execute(select(Reservation).where(Reservation.id == reservation_id))
    return result.scalar_one_or_none()


async def list_reservations_for_item(session: AsyncSession, item_id: UUID) -> list[Reservation]:
    result = await session.execute(
        select(Reservation).where(Reservation.item_id == item_id).order_by(Reservation.created_at)
    )
    return list(result.scalars().all())


async def total_reserved_for_item(session: AsyncSession, item_id: UUID) -> Decimal:
    result = await session.execute(
        select(func.coalesce(func.sum(Reservation.amount), 0)).where(Reservation.item_id == item_id)
    )
    return result.scalar() or Decimal("0")


async def create_reservation(
    session: AsyncSession,
    item_id: UUID,
    amount: float,
    is_full_reservation: bool = False,
    user_id: UUID | None = None,
    guest_name: str | None = None,
) -> Reservation:
    """Create reservation inside a transaction. Caller must run in transaction to avoid double reserve."""
    item_result = await session.execute(select(Item).where(Item.id == item_id))
    item = item_result.scalar_one_or_none()
    if not item:
        raise ValueError("Item not found")

    total = await total_reserved_for_item(session, item_id)
    item_price = float(item.price or 0)
    if item_price > 0 and total + amount > item_price:
        raise ValueError("Reservation would exceed item price")

    reservation = Reservation(
        item_id=item_id,
        user_id=user_id,
        guest_name=guest_name,
        amount=amount,
        is_full_reservation=is_full_reservation,
    )
    session.add(reservation)
    await session.flush()
    await session.refresh(reservation)
    return reservation
