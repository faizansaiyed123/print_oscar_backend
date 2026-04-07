from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr

from app.schemas.common import ORMModel, TimestampedSchema


class DashboardMetrics(BaseModel):
    total_sales: Decimal
    total_orders: int
    total_customers: int
    low_stock_products: int


class SalesPoint(BaseModel):
    period: str
    revenue: Decimal
    orders: int


class CouponWrite(BaseModel):
    code: str
    description: str | None = None
    discount_type: str
    discount_value: Decimal
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    usage_limit: int | None = None
    min_order_amount: Decimal | None = None
    applies_to_all_products: bool = True
    product_ids: list[int] = []
    is_active: bool = True


class CouponRead(TimestampedSchema):
    id: int
    code: str
    description: str | None = None
    discount_type: str
    discount_value: Decimal
    is_active: bool
    usage_limit: int | None = None
    usage_count: int


class ShippingMethodWrite(BaseModel):
    code: str
    name: str
    description: str | None = None
    base_rate: Decimal = Decimal("0.00")
    estimated_days: int | None = None
    is_enabled: bool = True


class ShippingMethodRead(TimestampedSchema):
    id: int
    code: str
    name: str
    description: str | None = None
    base_rate: Decimal
    estimated_days: int | None = None
    is_enabled: bool


class ShippingRateRuleWrite(BaseModel):
    shipping_method_id: int
    country_code: str | None = None
    state: str | None = None
    zip_prefix: str | None = None
    min_order_amount: Decimal | None = None
    extra_charge: Decimal = Decimal("0.00")
    is_active: bool = True


class ShippingRateRuleRead(TimestampedSchema):
    id: int
    shipping_method_id: int
    country_code: str | None = None
    state: str | None = None
    zip_prefix: str | None = None
    min_order_amount: Decimal | None = None
    extra_charge: Decimal
    is_active: bool


class TaxRuleWrite(BaseModel):
    country_code: str = "US"
    state: str | None = None
    zip_prefix: str | None = None
    rate_percent: Decimal
    is_active: bool = True


class TaxRuleRead(TimestampedSchema):
    id: int
    country_code: str
    state: str | None = None
    zip_prefix: str | None = None
    rate_percent: Decimal
    is_active: bool


class InventoryAdjustmentWrite(BaseModel):
    product_id: int
    variant_id: int | None = None
    quantity_delta: int
    movement_type: str
    warehouse_name: str | None = None
    reason: str | None = None


class InventoryMovementRead(TimestampedSchema):
    id: int
    product_id: int
    variant_id: int | None = None
    warehouse_name: str | None = None
    movement_type: str
    quantity_delta: int
    balance_after: int | None = None
    reason: str | None = None
    created_by_user_id: int | None = None


class StoreSettingWrite(BaseModel):
    key: str
    value: str | None = None
    is_public: bool = False


class StoreSettingRead(TimestampedSchema):
    key: str
    value: str | None = None
    is_public: bool


class BannerWrite(BaseModel):
    title: str
    image_url: str
    target_url: str | None = None
    is_active: bool = True


class BannerRead(TimestampedSchema):
    id: int
    title: str
    image_url: str
    target_url: str | None = None
    is_active: bool


class CampaignWrite(BaseModel):
    name: str
    description: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    is_active: bool = True


class CampaignRead(TimestampedSchema):
    id: int
    name: str
    description: str | None = None
    is_active: bool


class RedirectRuleWrite(BaseModel):
    source_path: str
    target_path: str
    status_code: int = 301
    is_active: bool = True


class RedirectRuleRead(TimestampedSchema):
    id: int
    source_path: str
    target_path: str
    status_code: int
    is_active: bool


class PermissionRead(ORMModel):
    id: int
    name: str
    description: str | None = None


class RoleWrite(BaseModel):
    name: str
    description: str | None = None
    permission_ids: list[int] = []


class RoleRead(ORMModel):
    id: int
    name: str
    description: str | None = None
    permissions: list[PermissionRead] = []


class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone_number: str | None = None
    role_ids: list[int] = []


class CustomerEmailRequest(BaseModel):
    subject: str
    body: str


class BulkPriceUpdateItem(BaseModel):
    product_id: int
    price: Decimal


class BulkStockUpdateItem(BaseModel):
    product_id: int
    variant_id: int | None = None
    stock_quantity: int
