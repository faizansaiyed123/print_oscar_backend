from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_roles
from app.schemas.admin import BulkPriceUpdateItem, BulkStockUpdateItem
from app.schemas.catalog import CategoryRead, CategoryWrite, CustomizationRuleRead, CustomizationRuleWrite, ProductRead, ProductReviewModerationUpdate, ProductReviewRead, ProductWrite
from app.schemas.common import ActionResponse, PaginatedResponse
from app.services.catalog import CatalogService

router = APIRouter(dependencies=[Depends(require_roles("super_admin", "admin", "manager"))])


@router.get("/catalog/categories", response_model=list[CategoryRead])
async def admin_categories(session: AsyncSession = Depends(get_db)) -> list[CategoryRead]:
    service = CatalogService(session)
    categories = await service.list_categories()
    return [CategoryRead.model_validate(category) for category in categories]


@router.post("/catalog/categories", response_model=CategoryRead)
async def create_category(payload: CategoryWrite, session: AsyncSession = Depends(get_db)) -> CategoryRead:
    service = CatalogService(session)
    category = await service.create_category(payload)
    return CategoryRead.model_validate(category)


@router.put("/catalog/categories/{category_id}", response_model=CategoryRead)
async def update_category(category_id: int, payload: CategoryWrite, session: AsyncSession = Depends(get_db)) -> CategoryRead:
    service = CatalogService(session)
    category = await service.update_category(category_id, payload)
    return CategoryRead.model_validate(category)


@router.delete("/catalog/categories/{category_id}", response_model=ActionResponse)
async def delete_category(category_id: int, session: AsyncSession = Depends(get_db)) -> ActionResponse:
    service = CatalogService(session)
    await service.delete_category(category_id)
    return ActionResponse(message="Category deleted")


@router.get("/catalog/products", response_model=PaginatedResponse)
async def admin_products(page: int = 1, page_size: int = 20, search: str | None = None, session: AsyncSession = Depends(get_db)):
    service = CatalogService(session)
    items, total = await service.list_products(search=search, page=page, page_size=page_size)
    return PaginatedResponse(items=[ProductRead.model_validate(item) for item in items], total=total, page=page, page_size=page_size)


@router.post("/catalog/products", response_model=ProductRead)
async def create_product(payload: ProductWrite, session: AsyncSession = Depends(get_db)) -> ProductRead:
    service = CatalogService(session)
    product = await service.create_product(payload)
    return ProductRead.model_validate(product)


@router.put("/catalog/products/{product_id}", response_model=ProductRead)
async def update_product(product_id: int, payload: ProductWrite, session: AsyncSession = Depends(get_db)) -> ProductRead:
    service = CatalogService(session)
    product = await service.update_product(product_id, payload)
    return ProductRead.model_validate(product)


@router.delete("/catalog/products/{product_id}", response_model=ActionResponse)
async def delete_product(product_id: int, session: AsyncSession = Depends(get_db)) -> ActionResponse:
    service = CatalogService(session)
    await service.delete_product(product_id)
    return ActionResponse(message="Product deleted")


@router.post("/catalog/products/bulk-import", response_model=list[ProductRead])
async def bulk_import_products(payload: list[ProductWrite], session: AsyncSession = Depends(get_db)) -> list[ProductRead]:
    service = CatalogService(session)
    products = await service.bulk_import(payload)
    return [ProductRead.model_validate(product) for product in products]


@router.post("/catalog/products/bulk-price-update")
async def bulk_update_prices(payload: list[BulkPriceUpdateItem], session: AsyncSession = Depends(get_db)):
    service = CatalogService(session)
    products = await service.bulk_update_prices([item.model_dump() for item in payload])
    return {"updated_count": len(products)}


@router.post("/catalog/products/bulk-stock-update")
async def bulk_update_stock(payload: list[BulkStockUpdateItem], session: AsyncSession = Depends(get_db)):
    service = CatalogService(session)
    products = await service.bulk_update_stock([item.model_dump() for item in payload])
    return {"updated_count": len(products)}


@router.post("/catalog/products/bulk-delete", response_model=ActionResponse)
async def bulk_delete_products(payload: list[int], session: AsyncSession = Depends(get_db)) -> ActionResponse:
    service = CatalogService(session)
    await service.bulk_delete(payload)
    return ActionResponse(message="Products deleted")


@router.get("/reviews", response_model=PaginatedResponse)
async def review_queue(page: int = 1, page_size: int = 50, session: AsyncSession = Depends(get_db)):
    service = CatalogService(session)
    items, total = await service.list_reviews(page=page, page_size=page_size)
    return PaginatedResponse(items=[ProductReviewRead.model_validate(item) for item in items], total=total, page=page, page_size=page_size)


@router.patch("/reviews/{review_id}", response_model=ProductReviewRead)
async def moderate_review(review_id: int, payload: ProductReviewModerationUpdate, session: AsyncSession = Depends(get_db)) -> ProductReviewRead:
    service = CatalogService(session)
    review = await service.moderate_review(review_id, payload)
    return ProductReviewRead.model_validate(review)


@router.post("/catalog/products/{product_id}/customization-rules", response_model=CustomizationRuleRead)
async def add_customization_rule(product_id: int, payload: CustomizationRuleWrite, session: AsyncSession = Depends(get_db)) -> CustomizationRuleRead:
    service = CatalogService(session)
    rule = await service.add_customization_rule(product_id, payload)
    return CustomizationRuleRead.model_validate(rule)


@router.put("/catalog/customization-rules/{rule_id}", response_model=CustomizationRuleRead)
async def update_customization_rule(rule_id: int, payload: CustomizationRuleWrite, session: AsyncSession = Depends(get_db)) -> CustomizationRuleRead:
    service = CatalogService(session)
    rule = await service.update_customization_rule(rule_id, payload)
    return CustomizationRuleRead.model_validate(rule)


@router.delete("/catalog/customization-rules/{rule_id}", response_model=ActionResponse)
async def delete_customization_rule(rule_id: int, session: AsyncSession = Depends(get_db)) -> ActionResponse:
    service = CatalogService(session)
    await service.remove_customization_rule(rule_id)
    return ActionResponse(message="Customization rule removed")




