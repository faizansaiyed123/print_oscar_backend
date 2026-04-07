from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.catalog import ProductReviewRead, ProductRead
from app.schemas.common import ActionResponse
from app.schemas.user import AddressCreate, AddressRead, AddressUpdate, UserRead, UserUpdate
from app.services.catalog import CatalogService
from app.services.user import UserService

router = APIRouter()


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.put("/me", response_model=UserRead)
async def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> UserRead:
    service = UserService(session)
    user = await service.update_profile(current_user, payload.model_dump(exclude_none=True))
    return UserRead.model_validate(user)


@router.get("/me/addresses", response_model=list[AddressRead])
async def list_addresses(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[AddressRead]:
    service = UserService(session)
    addresses = await service.list_addresses(current_user.id)
    return [AddressRead.model_validate(address) for address in addresses]


@router.post("/me/addresses", response_model=AddressRead)
async def create_address(
    payload: AddressCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AddressRead:
    service = UserService(session)
    address = await service.create_address(current_user.id, payload)
    return AddressRead.model_validate(address)


@router.put("/me/addresses/{address_id}", response_model=AddressRead)
async def update_address(
    address_id: int,
    payload: AddressUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AddressRead:
    service = UserService(session)
    address = await service.update_address(current_user.id, address_id, payload)
    return AddressRead.model_validate(address)


@router.delete("/me/addresses/{address_id}", response_model=ActionResponse)
async def delete_address(
    address_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ActionResponse:
    service = UserService(session)
    await service.delete_address(current_user.id, address_id)
    return ActionResponse(message="Address deleted")


@router.get("/me/reviews", response_model=list[ProductReviewRead])
async def my_reviews(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[ProductReviewRead]:
    service = CatalogService(session)
    reviews, _ = await service.list_reviews(user_id=current_user.id, page=1, page_size=100)
    return [ProductReviewRead.model_validate(review) for review in reviews]


@router.get("/me/wishlist", response_model=list[ProductRead])
async def get_wishlist(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[ProductRead]:
    service = UserService(session)
    products = await service.get_wishlist(current_user.id)
    return [ProductRead.model_validate(product) for product in products]


@router.post("/me/wishlist/{product_id}", response_model=ProductRead)
async def add_to_wishlist(
    product_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProductRead:
    service = UserService(session)
    product = await service.add_to_wishlist(current_user.id, product_id)
    return ProductRead.model_validate(product)


@router.delete("/me/wishlist/{product_id}", response_model=ActionResponse)
async def remove_from_wishlist(
    product_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ActionResponse:
    service = UserService(session)
    await service.remove_from_wishlist(current_user.id, product_id)
    return ActionResponse(message="Product removed from wishlist")
