"""Product URL fetch: preview endpoint (OpenGraph parse). Fallback to manual input if parsing fails."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.product import ProductFetchRequest, ProductFetchResponse
from app.services.product_fetch import fetch_product

router = APIRouter(prefix="/product", tags=["product"])


@router.post("/fetch", response_model=ProductFetchResponse)
async def fetch_product_preview(
    data: ProductFetchRequest,
    user: User = Depends(get_current_user),
):
    """
    Fetch product URL and parse og:title, og:image, product:price:amount.
    Returns preview for form prefill; frontend falls back to manual input when success=false.
    """
    result = await fetch_product(data.url)
    if result is None:
        return ProductFetchResponse(
            success=False,
            error="Could not fetch or parse the URL. Use manual input.",
        )
    return ProductFetchResponse(
        success=True,
        title=result.title,
        image_url=result.image_url,
        price=result.price,
        currency=result.currency,
        snapshot=result.snapshot,
    )
