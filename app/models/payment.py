from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import Boolean, DateTime, DECIMAL, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class PaymentGateway(str, Enum):
    STRIPE = "stripe"
    PAYPAL = "paypal"
    ADYEN = "adyen"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentType(str, Enum):
    ONE_TIME = "one_time"
    RECURRING = "recurring"
    INSTALLMENT = "installment"


class PaymentMethod(str, Enum):
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    DIGITAL_WALLET = "digital_wallet"
    BUY_NOW_PAY_LATER = "buy_now_pay_later"


class Payment(Base, TimestampMixin):
    """Main payment record linked to orders."""
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    payment_gateway: Mapped[PaymentGateway] = mapped_column(String(50), nullable=False)
    gateway_payment_id: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    status: Mapped[PaymentStatus] = mapped_column(String(30), default=PaymentStatus.PENDING, index=True)
    payment_type: Mapped[PaymentType] = mapped_column(String(30), default=PaymentType.ONE_TIME)
    payment_method: Mapped[PaymentMethod] = mapped_column(String(50), nullable=True)
    
    # Financial amounts
    amount: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), default="USD")
    fee_amount: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), default=Decimal("0.00"))
    tax_amount: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), default=Decimal("0.00"))
    refunded_amount: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), default=Decimal("0.00"))
    
    # Timing
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Gateway response and metadata
    gateway_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    
    # Customer info for payment processing
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    
    # Relationships
    order: Mapped["Order"] = relationship(back_populates="payment")
    transactions: Mapped[list["PaymentTransaction"]] = relationship(
        back_populates="payment", cascade="all, delete-orphan"
    )
    refunds: Mapped[list["PaymentRefund"]] = relationship(
        back_populates="payment", cascade="all, delete-orphan"
    )
    method_details: Mapped["PaymentMethodDetails | None"] = relationship(
        back_populates="payment", uselist=False, cascade="all, delete-orphan"
    )


class PaymentTransaction(Base, TimestampMixin):
    """Individual transaction attempts for retry and audit purposes."""
    __tablename__ = "payment_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id", ondelete="CASCADE"), index=True)
    gateway_transaction_id: Mapped[str] = mapped_column(String(255), nullable=True)
    status: Mapped[PaymentStatus] = mapped_column(String(30), nullable=False)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    
    # Request and response data
    request_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    response_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Processing time
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    payment: Mapped["Payment"] = relationship(back_populates="transactions")


class PaymentRefund(Base, TimestampMixin):
    """Refund records linked to payments."""
    __tablename__ = "payment_refunds"

    id: Mapped[int] = mapped_column(primary_key=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id", ondelete="CASCADE"), index=True)
    gateway_refund_id: Mapped[str] = mapped_column(String(255), nullable=True)
    status: Mapped[PaymentStatus] = mapped_column(String(30), default=PaymentStatus.PENDING)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Gateway response
    gateway_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    payment: Mapped["Payment"] = relationship(back_populates="refunds")


class PaymentMethodDetails(Base, TimestampMixin):
    """Secure storage of payment method details (tokenized)."""
    __tablename__ = "payment_method_details"

    id: Mapped[int] = mapped_column(primary_key=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id", ondelete="CASCADE"), unique=True)
    method_type: Mapped[PaymentMethod] = mapped_column(String(50), nullable=False)
    
    # Tokenized/card details (NEVER store raw card data)
    payment_method_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    card_last4: Mapped[str | None] = mapped_column(String(4), nullable=True)
    card_brand: Mapped[str | None] = mapped_column(String(50), nullable=True)
    card_exp_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    card_exp_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Digital wallet details
    wallet_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    wallet_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Verification status
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Gateway-specific metadata
    gateway_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    
    payment: Mapped["Payment"] = relationship(back_populates="method_details")


class PaymentGatewayConfig(Base, TimestampMixin):
    """Configuration for each payment gateway."""
    __tablename__ = "payment_gateway_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    gateway: Mapped[PaymentGateway] = mapped_column(String(50), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_test_mode: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Priority for routing (lower number = higher priority)
    priority: Mapped[int] = mapped_column(Integer, default=1)
    
    # Configuration (encrypted in production)
    config_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # Rate limiting and throttling
    max_requests_per_minute: Mapped[int] = mapped_column(Integer, default=100)
    current_rate_limit: Mapped[int] = mapped_column(Integer, default=0)
    rate_limit_reset_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Health check status
    is_healthy: Mapped[bool] = mapped_column(Boolean, default=True)
    last_health_check: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    health_check_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class PaymentRoutingRule(Base, TimestampMixin):
    """Rules for intelligent payment routing."""
    __tablename__ = "payment_routing_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=1)
    
    # Rule conditions
    currency_codes: Mapped[list[str]] = mapped_column(JSONB, nullable=True)
    amount_min: Mapped[Decimal | None] = mapped_column(DECIMAL(12, 2), nullable=True)
    amount_max: Mapped[Decimal | None] = mapped_column(DECIMAL(12, 2), nullable=True)
    payment_methods: Mapped[list[str]] = mapped_column(JSONB, nullable=True)
    country_codes: Mapped[list[str]] = mapped_column(JSONB, nullable=True)
    
    # Gateway assignment
    primary_gateway: Mapped[PaymentGateway] = mapped_column(String(50), nullable=False)
    fallback_gateways: Mapped[list[PaymentGateway]] = mapped_column(JSONB, nullable=True)
    
    # Routing strategy
    routing_strategy: Mapped[str] = mapped_column(String(50), default="priority")  # priority, load_balance, geography
