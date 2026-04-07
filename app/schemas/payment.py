from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field, validator


class PaymentMethodCreate(BaseModel):
    """Schema for creating payment method details."""
    method_type: Literal["card", "bank_transfer", "digital_wallet", "buy_now_pay_later"]
    
    # Card details (tokenized at gateway)
    card_token: str | None = None
    card_last4: str | None = None
    card_brand: str | None = None
    card_exp_month: int | None = Field(None, ge=1, le=12)
    card_exp_year: int | None = None
    
    # Digital wallet details
    wallet_type: str | None = None
    wallet_email: str | None = None
    
    # Billing address for verification
    billing_address: dict[str, Any] | None = None


class PaymentCreate(BaseModel):
    """Schema for creating a payment."""
    order_id: int
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency_code: str = Field(default="USD", max_length=3)
    payment_method: PaymentMethodCreate
    customer_email: str
    customer_ip: str | None = None
    preferred_gateway: str | None = None
    payment_metadata: dict[str, Any] | None = None

    @validator('currency_code')
    def validate_currency(cls, v):
        return v.upper()


class PaymentUpdate(BaseModel):
    """Schema for updating payment status."""
    status: Literal["pending", "processing", "completed", "failed", "cancelled", "refunded", "partially_refunded"]
    gateway_payment_id: str | None = None
    gateway_response: dict[str, Any] | None = None
    failure_reason: str | None = None
    processed_at: datetime | None = None


class PaymentResponse(BaseModel):
    """Schema for payment response."""
    id: int
    order_id: int
    payment_gateway: str
    gateway_payment_id: str | None
    status: str
    payment_type: str
    payment_method: str | None
    amount: Decimal
    currency_code: str
    fee_amount: Decimal
    tax_amount: Decimal
    refunded_amount: Decimal
    processed_at: datetime | None
    expires_at: datetime | None
    customer_email: str
    failure_reason: str | None
    payment_metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentMethodResponse(BaseModel):
    """Schema for payment method details response."""
    id: int
    payment_id: int
    method_type: str
    card_last4: str | None
    card_brand: str | None
    card_exp_month: int | None
    card_exp_year: int | None
    wallet_type: str | None
    wallet_email: str | None
    is_verified: bool
    verification_method: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentTransactionResponse(BaseModel):
    """Schema for payment transaction response."""
    id: int
    payment_id: int
    gateway_transaction_id: str | None
    status: str
    amount: Decimal
    attempt_number: int
    error_message: str | None
    processed_at: datetime | None
    processing_time_ms: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentRefundCreate(BaseModel):
    """Schema for creating a refund."""
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    reason: str | None = None


class PaymentRefundResponse(BaseModel):
    """Schema for refund response."""
    id: int
    payment_id: int
    gateway_refund_id: str | None
    status: str
    amount: Decimal
    reason: str | None
    processed_at: datetime | None
    gateway_response: dict[str, Any] | None
    failure_reason: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentGatewayConfigResponse(BaseModel):
    """Schema for gateway configuration response."""
    id: int
    gateway: str
    is_active: bool
    is_test_mode: bool
    priority: int
    max_requests_per_minute: int
    current_rate_limit: int
    is_healthy: bool
    last_health_check: datetime | None
    health_check_message: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentRoutingRuleResponse(BaseModel):
    """Schema for routing rule response."""
    id: int
    name: str
    is_active: bool
    priority: int
    currency_codes: list[str] | None
    amount_min: Decimal | None
    amount_max: Decimal | None
    payment_methods: list[str] | None
    country_codes: list[str] | None
    primary_gateway: str
    fallback_gateways: list[str] | None
    routing_strategy: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentIntentResponse(BaseModel):
    """Schema for payment intent creation response."""
    client_secret: str
    payment_id: int
    gateway: str
    amount: Decimal
    currency_code: str
    status: str
    expires_at: datetime | None


class PaymentVerificationRequest(BaseModel):
    """Schema for payment verification request."""
    payment_id: int
    verification_method: Literal["3ds", "otp", "biometric", "manual"]
    verification_data: dict[str, Any] = {}


class PaymentVerificationResponse(BaseModel):
    """Schema for payment verification response."""
    payment_id: int
    status: str
    is_verified: bool
    verification_method: str
    next_action: dict[str, Any] | None = None
    error_message: str | None = None


class PaymentWebhookPayload(BaseModel):
    """Schema for incoming webhook payloads."""
    gateway: str
    event_type: str
    event_id: str
    signature: str
    payload: dict[str, Any]
    received_at: datetime


class PaymentHealthCheckResponse(BaseModel):
    """Schema for health check response."""
    gateway: str
    is_healthy: bool
    response_time_ms: int
    last_check: datetime
    error_message: str | None = None


class PaymentMetricsResponse(BaseModel):
    """Schema for payment metrics."""
    total_payments: int
    successful_payments: int
    failed_payments: int
    success_rate: float
    total_amount: Decimal
    average_amount: Decimal
    gateway_breakdown: dict[str, dict[str, Any]]
    period_start: datetime
    period_end: datetime
