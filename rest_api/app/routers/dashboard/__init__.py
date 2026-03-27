"""Dashboard router aggregation — all /api/dashboard/* endpoints."""

from fastapi import APIRouter

from rest_api.app.routers.dashboard.allergens import router as allergens_router
from rest_api.app.routers.dashboard.badges import router as badges_router
from rest_api.app.routers.dashboard.batch_price import router as batch_price_router
from rest_api.app.routers.dashboard.branch_products import router as branch_products_router
from rest_api.app.routers.dashboard.cooking_methods import router as cooking_methods_router
from rest_api.app.routers.dashboard.dietary_profiles import router as dietary_profiles_router
from rest_api.app.routers.dashboard.product_extended import router as product_extended_router
from rest_api.app.routers.dashboard.seals import router as seals_router

dashboard_router = APIRouter()

dashboard_router.include_router(allergens_router)
dashboard_router.include_router(dietary_profiles_router)
dashboard_router.include_router(cooking_methods_router)
dashboard_router.include_router(badges_router)
dashboard_router.include_router(seals_router)
dashboard_router.include_router(product_extended_router)
dashboard_router.include_router(branch_products_router)
dashboard_router.include_router(batch_price_router)

__all__ = ["dashboard_router"]
