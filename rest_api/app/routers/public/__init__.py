"""Public router aggregation — all /api/public/* endpoints (no auth required)."""

from fastapi import APIRouter

from rest_api.app.routers.public.allergens import router as allergens_router
from rest_api.app.routers.public.branches import router as branches_router
from rest_api.app.routers.public.menu import router as menu_router

public_router = APIRouter()

public_router.include_router(menu_router)
public_router.include_router(branches_router)
public_router.include_router(allergens_router)

__all__ = ["public_router"]
