




from pathlib import Path

from typing import List, Optional, Any
from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.checkout import OrderRead
from app.schemas.common import PaginatedResponse
from app.services.orders import OrderService
from app.services.catalog import CatalogService
from app.models.catalog import Category
from pydantic import BaseModel

class SearchSuggestionItem(BaseModel):
    type: str  # "product" or "category"
    label: str
    slug: str | None = None
    product_id: int | None = None
    category_id: int | None = None

router = APIRouter()


@router.get("/", response_model=PaginatedResponse)
async def my_orders(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    service = OrderService(session)
    items, total = await service.list_orders(current_user.id, page=page, page_size=page_size)
    return PaginatedResponse(
        items=[OrderRead.model_validate(order) for order in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/suggestions", response_model=list[SearchSuggestionItem])
async def search_suggestions(
    q: str = Query(..., min_length=2),
    session: AsyncSession = Depends(get_db)
):
    service = CatalogService(session)

    suggestions: List[SearchSuggestionItem] = []

    # Products
    products, _ = await service.list_products(search=q, page=1, page_size=5)
    for product in products:
        suggestions.append(SearchSuggestionItem(
            type="product",
            label=product.title,
            slug=getattr(product.metadata_record, "slug", None),
            product_id=product.id,
            category_id=None
        ))

    # Categories - simple filter
    categories = await service.list_categories()
    for category in categories[:5]:
        if q.lower() in category.name.lower():
            suggestions.append(SearchSuggestionItem(
                type="category",
                label=category.name,
                slug=getattr(category.metadata_record, "slug", None),
                category_id=category.id,
                product_id=None
            ))

    return suggestions


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(order_id: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)) -> OrderRead:
    service = OrderService(session)
    order = await service.get_order(order_id, user_id=current_user.id)
    return OrderRead.model_validate(order)


@router.post("/{order_id}/cancel", response_model=OrderRead)
async def cancel_order(
    order_id: int,
    reason: str | None = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> OrderRead:
    service = OrderService(session)
    order = await service.cancel_order(order_id, user_id=current_user.id, reason=reason)
    return OrderRead.model_validate(order)


@router.get("/{order_id}/track")
async def track_order(order_id: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    service = OrderService(session)
    return await service.track_order(order_id, user_id=current_user.id)


@router.get("/{order_id}/invoice")
async def invoice(order_id: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    service = OrderService(session)
    relative_path = await service.generate_invoice(order_id, user_id=current_user.id)
    absolute_path = Path(settings.media_root) / relative_path
    return FileResponse(path=absolute_path, filename=absolute_path.name, media_type="text/plain")




