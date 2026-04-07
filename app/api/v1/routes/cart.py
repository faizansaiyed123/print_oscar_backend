from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_current_user_optional, get_db
from app.models.user import User
from app.schemas.checkout import (
    CartCreate,
    CartItemCreate,
    CartItemUpdate,
    CartRead,
    CheckoutRequest,
    CouponApplyRequest,
    OrderRead,
    SavedItemRead,
    ShippingQuoteRequest,
)
from app.schemas.media import UploadedCustomerFileRead
from app.services.checkout import CheckoutService
from app.services.media import MediaService

router = APIRouter()


@router.post("/", response_model=CartRead)
async def create_cart(
    payload: CartCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> CartRead:
    service = CheckoutService(session)
    cart = await service.get_or_create_cart(payload, user_id=current_user.id if current_user else None)
    return CartRead.model_validate(cart)


@router.get("/saved", response_model=list[SavedItemRead])
async def list_saved_items(
    current_user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_db),
) -> list[SavedItemRead]:
    if not current_user:
        return []
    service = CheckoutService(session)
    items = await service.list_saved_items(current_user.id)
    return [SavedItemRead.model_validate(item) for item in items]


@router.get("/{cart_id}", response_model=CartRead)
async def get_cart(cart_id: int, coupon_code: str | None = None, session: AsyncSession = Depends(get_db)) -> CartRead:
    service = CheckoutService(session)
    cart = await service.get_cart(cart_id, coupon_code=coupon_code)
    return CartRead.model_validate(cart)


@router.post("/{cart_id}/items", response_model=CartRead)
async def add_item(cart_id: int, payload: CartItemCreate, session: AsyncSession = Depends(get_db)) -> CartRead:
    service = CheckoutService(session)
    cart = await service.add_cart_item(cart_id, payload)
    return CartRead.model_validate(cart)


@router.put("/{cart_id}/items/{item_id}", response_model=CartRead)
async def update_item(
    cart_id: int,
    item_id: int,
    payload: CartItemUpdate,
    session: AsyncSession = Depends(get_db),
) -> CartRead:
    service = CheckoutService(session)
    cart = await service.update_cart_item(cart_id, item_id, payload)
    return CartRead.model_validate(cart)


@router.delete("/{cart_id}/items/{item_id}", response_model=CartRead)
async def remove_item(cart_id: int, item_id: int, session: AsyncSession = Depends(get_db)) -> CartRead:
    service = CheckoutService(session)
    cart = await service.remove_cart_item(cart_id, item_id)
    return CartRead.model_validate(cart)


@router.post("/{cart_id}/items/{item_id}/save-for-later", response_model=SavedItemRead)
async def save_for_later(
    cart_id: int,
    item_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SavedItemRead:
    service = CheckoutService(session)
    item = await service.save_for_later(current_user.id, item_id, cart_id)
    return SavedItemRead.model_validate(item)





@router.delete("/saved/{item_id}")
async def delete_saved_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    service = CheckoutService(session)
    await service.remove_saved_item(current_user.id, item_id)
    return {"message": "Saved item removed"}


@router.post("/apply-coupon")
async def apply_coupon(payload: CouponApplyRequest, session: AsyncSession = Depends(get_db)):
    service = CheckoutService(session)
    return await service.apply_coupon(payload.cart_id, payload.coupon_code)


@router.post("/shipping-quotes")
async def shipping_quotes(payload: ShippingQuoteRequest, session: AsyncSession = Depends(get_db)):
    service = CheckoutService(session)
    return await service.quote_shipping(payload.cart_id, payload.state, payload.zip_code, payload.country_code)


@router.post("/uploads/customization", response_model=UploadedCustomerFileRead)
async def upload_customization_file(
    file: UploadFile = File(...),
    field_type: str = Form(...),
    product_id: int | None = Form(default=None),
    order_item_id: int | None = Form(default=None),
    current_user: User | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_db),
) -> UploadedCustomerFileRead:
    service = MediaService(session)
    uploaded = await service.upload_customer_file(
        file,
        field_type=field_type,
        order_item_id=order_item_id,
        user_id=current_user.id if current_user else None,
        product_id=product_id,
    )
    return UploadedCustomerFileRead.model_validate(uploaded)


@router.post("/checkout", response_model=OrderRead)
async def checkout(
    payload: CheckoutRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> OrderRead:
    service = CheckoutService(session)
    order = await service.checkout(current_user.id if current_user else None, payload)
    return OrderRead.model_validate(order)
