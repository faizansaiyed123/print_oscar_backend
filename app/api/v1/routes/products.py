from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.catalog import FilterOptions, ProductRead, ProductReviewCreate, ProductReviewRead
from app.schemas.common import PaginatedResponse
from app.services.catalog import CatalogService

router = APIRouter()


@router.get("/filters", response_model=FilterOptions)
async def get_filters(
    search: str | None = None,
    category_id: int | None = Query(None),
    min_price: Decimal | None = Query(None),
    max_price: Decimal | None = Query(None),
    size: str | None = None,
    session: AsyncSession = Depends(get_db),
):
    service = CatalogService(session)
    result = await service.get_filters(
        search=search,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        size=size,
    )
    return result


@router.get("/", response_model=PaginatedResponse)
async def list_products(
    search: str | None = None,
    category_id: int | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    size: str | None = None,
    sort_by: str = Query(default="newest", pattern="^(newest|price_asc|price_desc|popularity)$"),
    page: int = 1,
    page_size: int = 20,
    session: AsyncSession = Depends(get_db),
):
    service = CatalogService(session)
    items, total = await service.list_products(
        search=search,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        size=size,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[ProductRead.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/slug/{slug}", response_model=ProductRead)
async def get_product_by_slug(slug: str, session: AsyncSession = Depends(get_db)) -> ProductRead:
    service = CatalogService(session)
    product = await service.get_product(slug=slug)
    return ProductRead.model_validate(product)


@router.get("/{id_or_slug}", response_model=ProductRead)
async def get_product(id_or_slug: str, session: AsyncSession = Depends(get_db)) -> ProductRead:
    service = CatalogService(session)
    if id_or_slug.isdigit():
        product = await service.get_product(product_id=int(id_or_slug))
    else:
        product = await service.get_product(slug=id_or_slug)
    return ProductRead.model_validate(product)


@router.get("/{id_or_slug}/reviews", response_model=PaginatedResponse)
async def list_reviews(
    id_or_slug: str,
    page: int = 1,
    page_size: int = 20,
    session: AsyncSession = Depends(get_db),
):
    service = CatalogService(session)
    if id_or_slug.isdigit():
        product_id = int(id_or_slug)
    else:
        product = await service.get_product(slug=id_or_slug)
        product_id = product.id

    items, total = await service.list_reviews(product_id=product_id, page=page, page_size=page_size)
    return PaginatedResponse(
        items=[ProductReviewRead.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/{id_or_slug}/reviews", response_model=ProductReviewRead)
async def create_review(
    id_or_slug: str,
    payload: ProductReviewCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProductReviewRead:
    service = CatalogService(session)
    if id_or_slug.isdigit():
        product_id = int(id_or_slug)
    else:
        product = await service.get_product(slug=id_or_slug)
        product_id = product.id

    review = await service.add_review(product_id, current_user.id, payload)
    return ProductReviewRead.model_validate(review)


@router.post("/sync-metadata")
async def sync_metadata(session: AsyncSession = Depends(get_db)):
    """Maintenance endpoint to create missing metadata for products and categories"""
    service = CatalogService(session)
    return await service.sync_metadata()
