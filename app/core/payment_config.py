"""Payment configuration management."""

import os
from typing import Any, Dict, Optional

from pydantic import BaseSettings, Field


class PaymentSettings(BaseSettings):
    """Payment system configuration settings."""
    
    # General settings
    PAYMENT_ENABLED: bool = Field(default=True, description="Enable payment processing")
    PAYMENT_TEST_MODE: bool = Field(default=True, description="Use test mode for all gateways")
    PAYMENT_WEBHOOK_URL: str = Field(
        default="https://yourstore.com/api/v1/webhooks",
        description="Base URL for webhooks"
    )
    
    # Security settings
    PAYMENT_ENCRYPTION_KEY: Optional[str] = Field(
        default=None,
        description="Encryption key for sensitive data"
    )
    PAYMENT_HMAC_KEY: Optional[str] = Field(
        default=None,
        description="HMAC key for webhook verification"
    )
    
    # Retry settings
    PAYMENT_MAX_RETRIES: int = Field(default=3, description="Maximum retry attempts")
    PAYMENT_RETRY_DELAY: int = Field(default=2, description="Base retry delay in seconds")
    PAYMENT_RETRY_STRATEGY: str = Field(
        default="exponential_backoff",
        description="Retry strategy: immediate, exponential_backoff, linear_backoff, fixed_interval"
    )
    
    # Rate limiting
    PAYMENT_RATE_LIMIT_PER_MINUTE: int = Field(
        default=100,
        description="Rate limit per minute per gateway"
    )
    
    # Fraud detection
    PAYMENT_FRAUD_DETECTION_ENABLED: bool = Field(
        default=True,
        description="Enable basic fraud detection"
    )
    PAYMENT_HIGH_AMOUNT_THRESHOLD: float = Field(
        default=10000.0,
        description="Amount threshold for fraud detection"
    )
    
    # Circuit breaker
    PAYMENT_CIRCUIT_BREAKER_THRESHOLD: int = Field(
        default=5,
        description="Failure threshold for circuit breaker"
    )
    PAYMENT_CIRCUIT_BREAKER_TIMEOUT: int = Field(
        default=60,
        description="Circuit breaker recovery timeout in seconds"
    )
    
    # Stripe configuration
    STRIPE_ENABLED: bool = Field(default=True, description="Enable Stripe gateway")
    STRIPE_SECRET_KEY: Optional[str] = Field(
        default=None,
        description="Stripe secret API key"
    )
    STRIPE_PUBLISHABLE_KEY: Optional[str] = Field(
        default=None,
        description="Stripe publishable key"
    )
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(
        default=None,
        description="Stripe webhook secret"
    )
    STRIPE_TEST_SECRET_KEY: Optional[str] = Field(
        default="sk_test_...",
        description="Stripe test secret key"
    )
    STRIPE_TEST_PUBLISHABLE_KEY: Optional[str] = Field(
        default="pk_test_...",
        description="Stripe test publishable key"
    )
    
    # PayPal configuration
    PAYPAL_ENABLED: bool = Field(default=True, description="Enable PayPal gateway")
    PAYPAL_CLIENT_ID: Optional[str] = Field(
        default=None,
        description="PayPal client ID"
    )
    PAYPAL_CLIENT_SECRET: Optional[str] = Field(
        default=None,
        description="PayPal client secret"
    )
    PAYPAL_WEBHOOK_ID: Optional[str] = Field(
        default=None,
        description="PayPal webhook ID"
    )
    PAYPAL_RETURN_URL: str = Field(
        default="https://yourstore.com/payment/return",
        description="PayPal return URL"
    )
    PAYPAL_CANCEL_URL: str = Field(
        default="https://yourstore.com/payment/cancel",
        description="PayPal cancel URL"
    )
    PAYPAL_SANDBOX_CLIENT_ID: Optional[str] = Field(
        default="test_client_id",
        description="PayPal sandbox client ID"
    )
    PAYPAL_SANDBOX_CLIENT_SECRET: Optional[str] = Field(
        default="test_client_secret",
        description="PayPal sandbox client secret"
    )
    
    # Adyen configuration
    ADYEN_ENABLED: bool = Field(default=True, description="Enable Adyen gateway")
    ADYEN_API_KEY: Optional[str] = Field(
        default=None,
        description="Adyen API key"
    )
    ADYEN_MERCHANT_ACCOUNT: Optional[str] = Field(
        default=None,
        description="Adyen merchant account"
    )
    ADYEN_CLIENT_KEY: Optional[str] = Field(
        default=None,
        description="Adyen client key"
    )
    ADYEN_ENVIRONMENT: str = Field(
        default="test",
        description="Adyen environment: test or live"
    )
    ADYEN_HMAC_KEY: Optional[str] = Field(
        default=None,
        description="Adyen HMAC key for webhooks"
    )
    ADYEN_TEST_API_KEY: Optional[str] = Field(
        default="test_api_key",
        description="Adyen test API key"
    )
    ADYEN_TEST_MERCHANT_ACCOUNT: str = Field(
        default="TestMerchant",
        description="Adyen test merchant account"
    )
    ADYEN_TEST_CLIENT_KEY: Optional[str] = Field(
        default="test_client_key",
        description="Adyen test client key"
    )
    
    # Database settings
    PAYMENT_DB_POOL_SIZE: int = Field(
        default=10,
        description="Database pool size for payment operations"
    )
    
    # Monitoring and logging
    PAYMENT_LOG_LEVEL: str = Field(
        default="INFO",
        description="Payment system log level"
    )
    PAYMENT_METRICS_ENABLED: bool = Field(
        default=True,
        description="Enable payment metrics collection"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True


def get_payment_settings() -> PaymentSettings:
    """Get payment configuration settings."""
    return PaymentSettings()


def get_gateway_config(gateway_name: str, test_mode: bool = True) -> Dict[str, Any]:
    """Get configuration for a specific gateway."""
    settings = get_payment_settings()
    
    if gateway_name.lower() == "stripe":
        return {
            "api_key": settings.STRIPE_TEST_SECRET_KEY if test_mode else settings.STRIPE_SECRET_KEY,
            "publishable_key": settings.STRIPE_TEST_PUBLISHABLE_KEY if test_mode else settings.STRIPE_PUBLISHABLE_KEY,
            "webhook_secret": settings.STRIPE_WEBHOOK_SECRET,
            "max_retries": settings.PAYMENT_MAX_RETRIES,
        }
    
    elif gateway_name.lower() == "paypal":
        return {
            "client_id": settings.PAYPAL_SANDBOX_CLIENT_ID if test_mode else settings.PAYPAL_CLIENT_ID,
            "client_secret": settings.PAYPAL_SANDBOX_CLIENT_SECRET if test_mode else settings.PAYPAL_CLIENT_SECRET,
            "webhook_id": settings.PAYPAL_WEBHOOK_ID,
            "return_url": settings.PAYPAL_RETURN_URL,
            "cancel_url": settings.PAYPAL_CANCEL_URL,
            "test_mode": test_mode,
        }
    
    elif gateway_name.lower() == "adyen":
        return {
            "api_key": settings.ADYEN_TEST_API_KEY if test_mode else settings.ADYEN_API_KEY,
            "merchant_account": settings.ADYEN_TEST_MERCHANT_ACCOUNT if test_mode else settings.ADYEN_MERCHANT_ACCOUNT,
            "client_key": settings.ADYEN_TEST_CLIENT_KEY if test_mode else settings.ADYEN_CLIENT_KEY,
            "environment": "test" if test_mode else settings.ADYEN_ENVIRONMENT,
            "hmac_key": settings.ADYEN_HMAC_KEY,
            "webhook_username": os.getenv("ADYEN_WEBHOOK_USERNAME"),
            "webhook_password": os.getenv("ADYEN_WEBHOOK_PASSWORD"),
        }
    
    else:
        raise ValueError(f"Unknown gateway: {gateway_name}")


def validate_payment_config() -> Dict[str, Any]:
    """Validate payment configuration."""
    settings = get_payment_settings()
    issues = []
    warnings = []
    
    # Check required settings
    if settings.PAYMENT_ENABLED:
        # Check if at least one gateway is enabled
        gateways_enabled = sum([
            settings.STRIPE_ENABLED,
            settings.PAYPAL_ENABLED,
            settings.ADYEN_ENABLED,
        ])
        
        if gateways_enabled == 0:
            issues.append("No payment gateways are enabled")
        
        # Check Stripe configuration
        if settings.STRIPE_ENABLED:
            if settings.PAYMENT_TEST_MODE and not settings.STRIPE_TEST_SECRET_KEY:
                issues.append("Stripe test secret key is missing")
            elif not settings.PAYMENT_TEST_MODE and not settings.STRIPE_SECRET_KEY:
                issues.append("Stripe production secret key is missing")
        
        # Check PayPal configuration
        if settings.PAYPAL_ENABLED:
            if settings.PAYMENT_TEST_MODE:
                if not settings.PAYPAL_SANDBOX_CLIENT_ID:
                    issues.append("PayPal sandbox client ID is missing")
                if not settings.PAYPAL_SANDBOX_CLIENT_SECRET:
                    issues.append("PayPal sandbox client secret is missing")
            else:
                if not settings.PAYPAL_CLIENT_ID:
                    issues.append("PayPal production client ID is missing")
                if not settings.PAYPAL_CLIENT_SECRET:
                    issues.append("PayPal production client secret is missing")
        
        # Check Adyen configuration
        if settings.ADYEN_ENABLED:
            if settings.PAYMENT_TEST_MODE and not settings.ADYEN_TEST_API_KEY:
                issues.append("Adyen test API key is missing")
            elif not settings.PAYMENT_TEST_MODE and not settings.ADYEN_API_KEY:
                issues.append("Adyen production API key is missing")
    
    # Check security settings
    if not settings.PAYMENT_ENCRYPTION_KEY and not settings.PAYMENT_TEST_MODE:
        warnings.append("Payment encryption key is not set in production")
    
    if not settings.PAYMENT_HMAC_KEY and not settings.PAYMENT_TEST_MODE:
        warnings.append("Payment HMAC key is not set in production")
    
    # Check URLs
    if "localhost" in settings.PAYMENT_WEBHOOK_URL and not settings.PAYMENT_TEST_MODE:
        warnings.append("Webhook URL points to localhost in production")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "enabled_gateways": [
            gateway for gateway, enabled in [
                ("stripe", settings.STRIPE_ENABLED),
                ("paypal", settings.PAYPAL_ENABLED),
                ("adyen", settings.ADYEN_ENABLED),
            ] if enabled
        ],
    }


def get_payment_environment_info() -> Dict[str, Any]:
    """Get information about the payment environment."""
    settings = get_payment_settings()
    
    return {
        "environment": "test" if settings.PAYMENT_TEST_MODE else "production",
        "payment_enabled": settings.PAYMENT_ENABLED,
        "fraud_detection_enabled": settings.PAYMENT_FRAUD_DETECTION_ENABLED,
        "metrics_enabled": settings.PAYMENT_METRICS_ENABLED,
        "max_retries": settings.PAYMENT_MAX_RETRIES,
        "retry_strategy": settings.PAYMENT_RETRY_STRATEGY,
        "circuit_breaker_threshold": settings.PAYMENT_CIRCUIT_BREAKER_THRESHOLD,
        "rate_limit_per_minute": settings.PAYMENT_RATE_LIMIT_PER_MINUTE,
        "high_amount_threshold": settings.PAYMENT_HIGH_AMOUNT_THRESHOLD,
    }
