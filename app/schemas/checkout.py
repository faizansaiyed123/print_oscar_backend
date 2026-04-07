from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMModel, TimestampedSchema


class CartCreate(BaseModel):
    session_key: str | None = None
    guest_email: EmailStr | None = None


class CartItemCreate(BaseModel):
    product_id: int
    variant_id: int | None = None
    quantity: int = 1
    customization_payload: dict | None = None


class CartItemUpdate(BaseModel):
    quantity: int
    customization_payload: dict | None = None


class CartItemRead(TimestampedSchema):
    id: int
    product_id: int
    variant_id: int | None = None
    quantity: int
    unit_price: Decimal
    customization_payload: dict | None = None


class CartTotals(ORMModel):
    subtotal: Decimal
    discount: Decimal
    shipping: Decimal
    tax: Decimal
    total: Decimal


class CartRead(TimestampedSchema):
    id: int
    user_id: int | None = None
    session_key: str | None = None
    currency_code: str
    guest_email: EmailStr | None = None
    items: list[CartItemRead] = []
    totals: CartTotals | None = None


class SavedItemCreate(BaseModel):
    product_id: int
    variant_id: int | None = None


class SavedItemRead(TimestampedSchema):
    id: int
    user_id: int
    product_id: int
    variant_id: int | None = None


class CouponApplyRequest(BaseModel):
    cart_id: int
    coupon_code: str


class ShippingQuoteRequest(BaseModel):
    cart_id: int
    state: str
    zip_code: str
    country_code: str = Field(default="US", min_length=2, max_length=2)


class CheckoutAddress(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    street_address: str
    apartment: str | None = None
    city: str
    state: str
    zip_code: str
    country_code: str = Field(default="US", min_length=2, max_length=2)


class CheckoutRequest(BaseModel):
    cart_id: int
    shipping_address: CheckoutAddress
    billing_address: CheckoutAddress
    shipping_method: str
    payment_method: str
    coupon_code: str | None = None
    notes: str | None = None
    create_account: bool = False
    account_password: str | None = None


class OrderItemRead(TimestampedSchema):
    id: int
    product_id: int | None = None
    variant_id: int | None = None
    product_title: str
    sku: str | None = None
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    customization_payload: dict | None = None


class OrderAddressRead(TimestampedSchema):
    id: int
    address_type: str
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    street_address: str
    apartment: str | None = None
    city: str
    state: str
    zip_code: str
    country_code: str


class OrderShipmentRead(TimestampedSchema):
    id: int
    shipping_method: str
    shipping_zone: str | None = None
    tracking_number: str | None = None
    label_url: str | None = None


class OrderRead(TimestampedSchema):
    id: int
    order_number: str
    status: str
    payment_status: str
    payment_method: str | None = None
    shipping_status: str
    subtotal_amount: Decimal
    discount_amount: Decimal
    shipping_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    refunded_amount: Decimal
    coupon_code: str | None = None
    tracking_number: str | None = None
    notes: str | None = None
    items: list[OrderItemRead] = []
    addresses: list[OrderAddressRead] = []
    shipment: OrderShipmentRead | None = None


class OrderStatusUpdate(BaseModel):
    status: str | None = None
    payment_status: str | None = None
    shipping_status: str | None = None
    tracking_number: str | None = None
    cancellation_reason: str | None = None
    refund_amount: Decimal | None = None
    notes: str | None = None
