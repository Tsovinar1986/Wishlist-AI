"""Server-side product auto-fetch: fetch URL, parse OpenGraph meta, return snapshot. Uses httpx + BeautifulSoup."""

import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup


@dataclass
class ProductSnapshot:
    """Parsed product data from a page. Safe to cache in DB."""

    title: str | None
    image_url: str | None
    price: float | None
    currency: str | None
    snapshot: dict  # Full parsed meta for cached_snapshot_json


def _get_meta_content(soup: BeautifulSoup, props: list[tuple[str, str]]) -> str | None:
    """Get content of first matching meta tag. props: [(attr, value), ...] e.g. [("property", "og:title")]."""
    for attr, value in props:
        tag = soup.find("meta", attrs={attr: value})
        if tag and tag.get("content"):
            return tag["content"].strip()
    return None


def _parse_price(value: str | None) -> tuple[float | None, str | None]:
    """Parse price string; return (amount, currency). Handles '12.34', '12,34', 'USD 12.34'."""
    if not value or not value.strip():
        return None, None
    value = value.strip()
    # Try to extract number (allow comma as decimal separator)
    match = re.search(r"(\d+[.,]?\d*)", value.replace(",", "."))
    if not match:
        return None, None
    try:
        amount = float(match.group(1).replace(",", "."))
    except ValueError:
        return None, None
    currency_match = re.search(r"([A-Z]{3})\b", value)
    currency = currency_match.group(1) if currency_match else None
    return amount, currency


def _absolute_url(base_url: str, path: str | None) -> str | None:
    if not path or not path.strip():
        return None
    path = path.strip()
    if path.startswith(("http://", "https://")):
        return path
    try:
        return urljoin(base_url, path)
    except Exception:
        return None


async def fetch_product(url: str, *, timeout: float = 10.0) -> ProductSnapshot | None:
    """
    Fetch page HTML and parse OpenGraph + product meta.
    - og:title, og:image, product:price:amount (and product:price:currency).
    Returns ProductSnapshot or None on fetch/parse failure (caller falls back to manual input).
    """
    if not url or not url.strip():
        return None
    url = url.strip()
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
            headers={"User-Agent": "WishlistAI/1.0 (Product preview fetcher)"},
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text
            base_url = str(resp.url)
    except (httpx.HTTPError, httpx.TimeoutException, Exception):
        return None

    soup = BeautifulSoup(html, "html.parser")

    # OpenGraph
    title = _get_meta_content(soup, [("property", "og:title"), ("name", "og:title")])
    image_url = _get_meta_content(soup, [("property", "og:image"), ("name", "og:image")])
    if image_url:
        image_url = _absolute_url(base_url, image_url)

    # Product meta (e.g. product:price:amount, product:price:currency)
    price_amount_str = _get_meta_content(
        soup,
        [
            ("property", "product:price:amount"),
            ("name", "product:price:amount"),
            ("property", "og:price:amount"),
            ("name", "og:price:amount"),
        ],
    )
    price_currency_str = _get_meta_content(
        soup,
        [
            ("property", "product:price:currency"),
            ("name", "product:price:currency"),
            ("property", "og:price:currency"),
            ("name", "og:price:currency"),
        ],
    )
    price, currency = _parse_price(price_amount_str)
    if price is not None and price_currency_str and not currency:
        currency = price_currency_str.strip().upper()[:3]

    # Build snapshot for DB cache
    snapshot = {
        "og_title": title,
        "og_image": image_url,
        "product_price_amount": price_amount_str,
        "product_price_currency": currency,
        "price_parsed": price,
        "fetched_url": base_url,
    }

    return ProductSnapshot(
        title=title,
        image_url=image_url,
        price=price,
        currency=currency,
        snapshot=snapshot,
    )
