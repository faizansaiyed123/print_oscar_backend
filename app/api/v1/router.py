from fastapi import APIRouter

from app.api.v1.routes import (
    admin_catalog,
    admin_customers,
    admin_dashboard,
    admin_operations,
    admin_orders,
    auth,
    banners,
    cart,
    categories,
    orders,
    payments,
    products,
    settings,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(cart.router, prefix="/cart", tags=["cart"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(banners.router, prefix="/banners", tags=["banners"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(admin_dashboard.router, prefix="/admin", tags=["admin"])
api_router.include_router(admin_catalog.router, prefix="/admin", tags=["admin"])
api_router.include_router(admin_orders.router, prefix="/admin", tags=["admin"])
api_router.include_router(admin_customers.router, prefix="/admin", tags=["admin"])
api_router.include_router(admin_operations.router, prefix="/admin", tags=["admin"])
