"""FastAPI application: CORS, routers, WebSocket."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
from app.models import Item, Reservation, User, Wishlist  # noqa: F401 - register with Base.metadata
from app.routers import auth, items, product, public, pusher_auth, reservations, users, wishlists, ws

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables if missing (e.g. first deploy on Railway; idempotent)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Wishlist AI API",
    description="Real-time wishlist backend with JWT auth and public slug URLs",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: allow http://localhost:3000 (frontend) and * for dev so API calls don't fail
cors_origins = settings.cors_origins_list
allow_all = cors_origins == ["*"] or (len(cors_origins) == 1 and cors_origins[0] == "*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if not allow_all else ["*"],
    allow_credentials=not allow_all,  # must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(product.router, prefix="/api")
app.include_router(wishlists.router, prefix="/api")
app.include_router(items.router, prefix="/api")
app.include_router(reservations.router, prefix="/api")
app.include_router(public.router, prefix="/api")
app.include_router(ws.router, prefix="/api")
app.include_router(pusher_auth.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
