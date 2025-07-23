from fastapi import APIRouter
from .admin import admin_router
from .products import product_router
from .payments import payment_router
from .orders import router as orders_router
from .cart import router as cart_router
from .auth import router as auth_router
from .admin import admin_router
from .address import router as address_router
from .analytics import router as analytics_router
from api.profile import router as profile_router


api_version_one = APIRouter(prefix="/api/v1")
api_version_one.include_router(auth_router)
api_version_one.include_router(profile_router)
api_version_one.include_router(product_router)
api_version_one.include_router(orders_router)
api_version_one.include_router(cart_router)
api_version_one.include_router(payment_router)
api_version_one.include_router(address_router)
api_version_one.include_router(analytics_router)
api_version_one.include_router(admin_router)
