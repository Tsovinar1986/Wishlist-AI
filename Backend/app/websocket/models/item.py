"""Item model (wishlist entry)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    wishlist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wishlists.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    product_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    allow_contributions: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    cached_snapshot_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    wishlist: Mapped["Wishlist"] = relationship("Wishlist", back_populates="items")
    reservations: Mapped[list["Reservation"]] = relationship(
        "Reservation", back_populates="item", lazy="selectin", cascade="all, delete-orphan"
    )
