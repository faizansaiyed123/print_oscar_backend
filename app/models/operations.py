from decimal import Decimal

from sqlalchemy import Boolean, DECIMAL, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ShippingMethod(Base, TimestampMixin):
    __tablename__ = "shipping_methods"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    base_rate: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), default=Decimal("0.00"), nullable=False)
    estimated_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ShippingRateRule(Base, TimestampMixin):
    __tablename__ = "shipping_rate_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    shipping_method_id: Mapped[int] = mapped_column(ForeignKey("shipping_methods.id", ondelete="CASCADE"), index=True)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    zip_prefix: Mapped[str | None] = mapped_column(String(20), nullable=True)
    min_order_amount: Mapped[Decimal | None] = mapped_column(DECIMAL(12, 2), nullable=True)
    extra_charge: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), default=Decimal("0.00"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class TaxRule(Base, TimestampMixin):
    __tablename__ = "tax_rules"
    __table_args__ = (UniqueConstraint("country_code", "state", "zip_prefix", name="uq_tax_rules_scope"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    country_code: Mapped[str] = mapped_column(String(2), default="US")
    state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    zip_prefix: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rate_percent: Mapped[Decimal] = mapped_column(DECIMAL(5, 2), default=Decimal("0.00"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class InventoryMovement(Base, TimestampMixin):
    __tablename__ = "inventory_movements"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    variant_id: Mapped[int | None] = mapped_column(ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True)
    warehouse_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    movement_type: Mapped[str] = mapped_column(String(30))
    quantity_delta: Mapped[int] = mapped_column(Integer)
    balance_after: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class RedirectRule(Base, TimestampMixin):
    __tablename__ = "redirect_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_path: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    target_path: Mapped[str] = mapped_column(String(255))
    status_code: Mapped[int] = mapped_column(Integer, default=301, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
