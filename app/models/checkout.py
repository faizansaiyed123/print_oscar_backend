from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, DECIMAL, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Cart(Base, TimestampMixin):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    session_key: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True, index=True)
    currency_code: Mapped[str] = mapped_column(String(3), default="USD")
    guest_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    items: Mapped[list["CartItem"]] = relationship(back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base, TimestampMixin):
    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("cart_id", "product_id", "variant_id", name="uq_cart_items_unique_product_variant"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    variant_id: Mapped[int | None] = mapped_column(ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False)
    customization_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    cart: Mapped["Cart"] = relationship(back_populates="items")


class SavedItem(Base, TimestampMixin):
    __tablename__ = "saved_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    variant_id: Mapped[int | None] = mapped_column(ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True)


class Coupon(Base, TimestampMixin):
    __tablename__ = "coupons"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    discount_type: Mapped[str] = mapped_column(String(30))
    discount_value: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    usage_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    min_order_amount: Mapped[Decimal | None] = mapped_column(DECIMAL(12, 2), nullable=True)
    applies_to_all_products: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    products: Mapped[list["CouponProduct"]] = relationship(back_populates="coupon", cascade="all, delete-orphan")


class CouponProduct(Base):
    __tablename__ = "coupon_products"
    __table_args__ = (UniqueConstraint("coupon_id", "product_id", name="uq_coupon_products_pair"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    coupon_id: Mapped[int] = mapped_column(ForeignKey("coupons.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)

    coupon: Mapped["Coupon"] = relationship(back_populates="products")


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    order_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    payment_status: Mapped[str] = mapped_column(String(30), default="pending")
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    shipping_status: Mapped[str] = mapped_column(String(30), default="pending")
    currency_code: Mapped[str] = mapped_column(String(3), default="USD")
    subtotal_amount: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), default=Decimal("0.00"), nullable=False)
    shipping_amount: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), default=Decimal("0.00"), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), default=Decimal("0.00"), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False)
    refunded_amount: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), default=Decimal("0.00"), nullable=False)
    coupon_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    addresses: Mapped[list["OrderAddress"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    shipment: Mapped["OrderShipment | None"] = relationship(back_populates="order", uselist=False, cascade="all, delete-orphan")
    status_history: Mapped[list["OrderStatusHistory"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    payment: Mapped["Payment | None"] = relationship(back_populates="order", uselist=False, cascade="all, delete-orphan")


class OrderItem(Base, TimestampMixin):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    variant_id: Mapped[int | None] = mapped_column(ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True)
    product_title: Mapped[str] = mapped_column(String(255))
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False)
    customization_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    order: Mapped["Order"] = relationship(back_populates="items")


class OrderAddress(Base, TimestampMixin):
    __tablename__ = "order_addresses"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    address_type: Mapped[str] = mapped_column(String(30))
    first_name: Mapped[str] = mapped_column(String(120))
    last_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255))
    phone_number: Mapped[str] = mapped_column(String(30))
    street_address: Mapped[str] = mapped_column(String(255))
    apartment: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(120))
    state: Mapped[str] = mapped_column(String(120))
    zip_code: Mapped[str] = mapped_column(String(20))
    country_code: Mapped[str] = mapped_column(String(2), default="US")

    order: Mapped["Order"] = relationship(back_populates="addresses")


class OrderShipment(Base, TimestampMixin):
    __tablename__ = "order_shipments"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), unique=True)
    shipping_method: Mapped[str] = mapped_column(String(120))
    shipping_zone: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    label_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    order: Mapped["Order"] = relationship(back_populates="shipment")


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(30))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    order: Mapped["Order"] = relationship(back_populates="status_history")
