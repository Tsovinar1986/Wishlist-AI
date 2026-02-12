"""Product fetch (preview) schemas."""

from pydantic import BaseModel


class ProductFetchRequest(BaseModel):
    url: str


class ProductFetchResponse(BaseModel):
    """Preview from URL. Use for form prefill; fallback to manual input if parsing failed."""

    success: bool
    title: str | None = None
    image_url: str | None = None
    price: float | None = None
    currency: str | None = None
    snapshot: dict | None = None
    error: str | None = None
