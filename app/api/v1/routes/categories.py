from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.schemas.catalog import CategoryRead, CategoryTreeRead
from app.services.catalog import CatalogService

router = APIRouter()


# def _build_tree(nodes, parent_id=None):
#     branch = []
#     for node in [item for item in nodes if item.parent_id == parent_id]:
#         data = CategoryTreeRead.model_validate(node).model_dump()
#         data["children"] = _build_tree(nodes, node.id)
#         branch.append(CategoryTreeRead(**data))
#     return branch


@router.get("/", response_model=list[CategoryRead])
async def list_categories(session: AsyncSession = Depends(get_db)) -> list[CategoryRead]:
    service = CatalogService(session)
    categories = await service.list_categories()
    return [CategoryRead.model_validate(category) for category in categories]


@router.get("/tree")
async def category_tree(session: AsyncSession = Depends(get_db)) -> list[CategoryTreeRead]:
    service = CatalogService(session)
    categories = await service.list_categories()

    return categories  # ✅ just return directly

@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(category_id: int, session: AsyncSession = Depends(get_db)) -> CategoryRead:
    service = CatalogService(session)
    category = await service.get_category(category_id)
    return CategoryRead.model_validate(category)
