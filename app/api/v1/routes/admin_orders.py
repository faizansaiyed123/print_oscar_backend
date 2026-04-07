from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db, require_roles
from app.schemas.checkout import OrderRead, OrderStatusUpdate
from app.schemas.common import ActionResponse
from app.schemas.common import PaginatedResponse
from app.schemas.media import UploadedCustomerFileRead
from app.services.admin import AdminService
from app.services.media import MediaService
from app.services.orders import OrderService

router = APIRouter(dependencies=[Depends(require_roles("super_admin", "admin", "manager"))])


@router.get("/orders", response_model=PaginatedResponse)
async def admin_orders(page: int = 1, page_size: int = 20, session: AsyncSession = Depends(get_db)):
    service = OrderService(session)
    items, total = await service.repository.list_orders(page=page, page_size=page_size)
    return PaginatedResponse(items=[OrderRead.model_validate(item) for item in items], total=total, page=page, page_size=page_size)


@router.get("/orders/{order_id}", response_model=OrderRead)
async def admin_order_detail(order_id: int, session: AsyncSession = Depends(get_db)) -> OrderRead:
    service = OrderService(session)
    order = await service.get_order(order_id)
    return OrderRead.model_validate(order)


@router.patch("/orders/{order_id}", response_model=OrderRead)
async def admin_update_order(order_id: int, payload: OrderStatusUpdate, session: AsyncSession = Depends(get_db)) -> OrderRead:
    service = OrderService(session)
    order = await service.admin_update_order(order_id, payload.model_dump(exclude_none=True))
    return OrderRead.model_validate(order)


@router.get("/orders/{order_id}/invoice")
async def admin_invoice(order_id: int, session: AsyncSession = Depends(get_db)):
    service = OrderService(session)
    relative_path = await service.generate_invoice(order_id)
    absolute_path = Path(settings.media_root) / relative_path
    return FileResponse(path=absolute_path, filename=absolute_path.name, media_type="text/plain")


@router.get("/orders/{order_id}/shipping-label")
async def admin_shipping_label(order_id: int, session: AsyncSession = Depends(get_db)):
    service = OrderService(session)
    relative_path = await service.generate_shipping_label(order_id)
    absolute_path = Path(settings.media_root) / relative_path
    return FileResponse(path=absolute_path, filename=absolute_path.name, media_type="text/plain")


@router.get("/customer-files", response_model=PaginatedResponse)
async def customer_files(page: int = 1, page_size: int = 50, session: AsyncSession = Depends(get_db)):
    service = AdminService(session)
    items, total = await service.repository.list_uploaded_customer_files(page=page, page_size=page_size)
    return PaginatedResponse(items=[UploadedCustomerFileRead.model_validate(item) for item in items], total=total, page=page, page_size=page_size)


@router.get("/customer-files/{file_id}/download")
async def download_customer_file(file_id: int, session: AsyncSession = Depends(get_db)):
    service = AdminService(session)
    customer_file = await service.repository.get_uploaded_customer_file(file_id)
    if not customer_file:
        raise HTTPException(status_code=404, detail="Customer file not found")
    absolute_path = Path(settings.media_root) / customer_file.file_path
    return FileResponse(path=absolute_path, filename=customer_file.file_name, media_type=customer_file.mime_type)


@router.delete("/customer-files/{file_id}", response_model=ActionResponse)
async def delete_customer_file(file_id: int, session: AsyncSession = Depends(get_db)) -> ActionResponse:
    service = MediaService(session)
    await service.delete_customer_file(file_id)
    return ActionResponse(message="Customer file deleted")
