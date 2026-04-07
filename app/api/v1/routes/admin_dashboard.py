from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_roles
from app.schemas.admin import DashboardMetrics, SalesPoint
from app.schemas.common import PaginatedResponse
from app.services.admin import AdminService

router = APIRouter(dependencies=[Depends(require_roles("super_admin", "admin", "manager"))])


@router.get("/dashboard", response_model=DashboardMetrics)
async def dashboard(session: AsyncSession = Depends(get_db)) -> DashboardMetrics:
    service = AdminService(session)
    metrics = await service.dashboard()
    return DashboardMetrics.model_validate(metrics)


@router.get("/reports/sales", response_model=list[SalesPoint])
async def sales_report(session: AsyncSession = Depends(get_db)) -> list[SalesPoint]:
    service = AdminService(session)
    report = await service.sales_report()
    return [SalesPoint.model_validate(item) for item in report]


@router.get("/reports/customers")
async def customer_growth_report(session: AsyncSession = Depends(get_db)):
    service = AdminService(session)
    return await service.customer_growth_report()


@router.get("/reports/products")
async def product_performance_report(session: AsyncSession = Depends(get_db)):
    service = AdminService(session)
    return await service.product_performance_report()


@router.get("/activity-logs", response_model=PaginatedResponse)
async def activity_logs(page: int = 1, page_size: int = 50, session: AsyncSession = Depends(get_db)):
    service = AdminService(session)
    items, total = await service.list_activity_logs(page=page, page_size=page_size)
    payload = [
        {
            "id": item.id,
            "admin_user_id": item.admin_user_id,
            "action": item.action,
            "entity_type": item.entity_type,
            "entity_id": item.entity_id,
            "details": item.details,
            "created_at": item.created_at,
        }
        for item in items
    ]
    return PaginatedResponse(items=payload, total=total, page=page, page_size=page_size)
