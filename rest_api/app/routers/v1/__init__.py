"""V1 router aggregation — all /api/v1/* endpoints."""

from fastapi import APIRouter

from rest_api.app.routers.v1.branches import router as branches_router
from rest_api.app.routers.v1.categories import router as categories_router
from rest_api.app.routers.v1.products import router as products_router
from rest_api.app.routers.v1.restaurants import router as restaurants_router
from rest_api.app.routers.v1.subcategories import router as subcategories_router

v1_router = APIRouter()

v1_router.include_router(restaurants_router)
v1_router.include_router(branches_router)
v1_router.include_router(categories_router)
v1_router.include_router(subcategories_router)
v1_router.include_router(products_router)

__all__ = ["v1_router"]
# force reload
