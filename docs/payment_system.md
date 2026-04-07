# Multi-Payment System Documentation

## Overview

This payment system provides a comprehensive, production-level solution for processing payments through multiple gateways (Stripe, PayPal, Adyen) with intelligent routing, failover mechanisms, and PCI compliance.

## Architecture

### Core Components

1. **Payment Models** (`app/models/payment.py`)
   - Payment, PaymentTransaction, PaymentRefund
   - PaymentMethodDetails, PaymentGatewayConfig
   - PaymentRoutingRule for intelligent routing

2. **Gateway Abstraction Layer** (`app/services/payment/gateway.py`)
   - Unified interface for all payment gateways
   - Standardized request/response handling
   - Common error handling and status mapping

3. **Gateway Implementations**
   - Stripe Gateway (`app/services/payment/stripe_gateway.py`)
   - PayPal Gateway (`app/services/payment/paypal_gateway.py`)
   - Adyen Gateway (`app/services/payment/adyen_gateway.py`)

4. **Smart Routing** (`app/services/payment/router.py`)
   - Geography-based routing for optimal performance
   - Load balancing options
   - Health checking and failover

5. **Payment Service** (`app/services/payment/service.py`)
   - Main orchestration layer
   - Transaction management
   - Webhook processing

6. **Security & Compliance** (`app/services/payment/security.py`)
   - PCI DSS compliance utilities
   - Data encryption and tokenization
   - Fraud detection
   - Webhook verification

7. **Retry & Failure Handling** (`app/services/payment/retry.py`)
   - Intelligent retry mechanisms
   - Circuit breaker pattern
   - Failure classification

## Features

### ✅ Multi-Gateway Support
- **Stripe**: Credit cards, digital wallets (Apple Pay, Google Pay)
- **PayPal**: PayPal accounts, bank transfers, Pay in 4
- **Adyen**: Global payment methods, local alternatives

### ✅ Intelligent Routing
- **Geography-based**: Optimal gateway selection by region
- **Load balancing**: Round-robin distribution
- **Health checking**: Automatic failover to healthy gateways
- **Rule-based**: Custom routing rules by amount, currency, method

### ✅ Security & Compliance
- **PCI DSS**: No raw card data storage
- **Encryption**: Sensitive data encryption at rest
- **Tokenization**: Secure payment method storage
- **Webhook verification**: Signature validation for all gateways
- **Fraud detection**: Basic velocity and pattern analysis

### ✅ Failure Handling
- **Automatic retries**: Configurable retry strategies
- **Circuit breaker**: Prevent cascade failures
- **Smart classification**: Temporary vs permanent failures
- **Fallback mechanisms**: Gateway switching on failure

### ✅ Global Optimization
- **Currency support**: 30+ currencies
- **Regional methods**: Local payment alternatives
- **Performance optimization**: Regional gateway selection
- **Compliance**: Regional regulation support

## API Endpoints

### Payment Operations

#### Create Payment
```http
POST /api/v1/payments
Content-Type: application/json

{
  "order_id": 123,
  "amount": 99.99,
  "currency_code": "USD",
  "payment_method": {
    "method_type": "card",
    "card_token": "pm_xxx"
  },
  "customer_email": "customer@example.com",
  "preferred_gateway": "stripe"
}
```

#### Confirm Payment
```http
POST /api/v1/payments/{payment_id}/confirm
Content-Type: application/json

{
  "payment_method": {
    "method_type": "card",
    "card_last4": "4242",
    "card_brand": "visa"
  }
}
```

#### Cancel Payment
```http
POST /api/v1/payments/{payment_id}/cancel
```

#### Process Refund
```http
POST /api/v1/payments/{payment_id}/refunds
Content-Type: application/json

{
  "amount": 50.00,
  "reason": "Customer requested refund"
}
```

#### Verify Payment (3D Secure)
```http
POST /api/v1/payments/{payment_id}/verify
Content-Type: application/json

{
  "verification_method": "3ds",
  "verification_data": {
    "payment_intent_id": "pi_xxx",
    "details": {
      "three_d_secure": {
        "authentication_value": "xxx"
      }
    }
  }
}
```

### Webhooks

#### Stripe Webhook
```http
POST /api/v1/webhooks/stripe
Stripe-Signature: signature-here
```

#### PayPal Webhook
```http
POST /api/v1/webhooks/paypal
PayPal-Auth-Algo: SHA256withRSA
PayPal-Transmission-Id: xxx
PayPal-Cert-Id: xxx
PayPal-Transmission-Sig: signature
PayPal-Transmission-Time: timestamp
```

#### Adyen Webhook
```http
POST /api/v1/webhooks/adyen
```

### Admin Endpoints

#### Get Payment Metrics
```http
GET /api/v1/admin/payments/metrics?gateway=stripe&start_date=2024-01-01
```

#### Get All Payments
```http
GET /api/v1/admin/payments?status=pending&limit=50
```

## Configuration

### Environment Variables

```bash
# General Settings
PAYMENT_ENABLED=true
PAYMENT_TEST_MODE=true
PAYMENT_WEBHOOK_URL=https://yourstore.com/api/v1/webhooks

# Security
PAYMENT_ENCRYPTION_KEY=your-32-char-encryption-key
PAYMENT_HMAC_KEY=your-hmac-key-for-webhooks

# Retry Configuration
PAYMENT_MAX_RETRIES=3
PAYMENT_RETRY_DELAY=2
PAYMENT_RETRY_STRATEGY=exponential_backoff

# Stripe
STRIPE_ENABLED=true
STRIPE_TEST_SECRET_KEY=sk_test_xxx
STRIPE_TEST_PUBLISHABLE_KEY=pk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# PayPal
PAYPAL_ENABLED=true
PAYPAL_SANDBOX_CLIENT_ID=xxx
PAYPAL_SANDBOX_CLIENT_SECRET=xxx
PAYPAL_RETURN_URL=https://yourstore.com/payment/return
PAYPAL_CANCEL_URL=https://yourstore.com/payment/cancel

# Adyen
ADYEN_ENABLED=true
ADYEN_TEST_API_KEY=xxx
ADYEN_TEST_MERCHANT_ACCOUNT=TestMerchant
ADYEN_TEST_CLIENT_KEY=xxx
```

### Gateway Priority Configuration

```python
# Regional gateway preferences
REGIONAL_PREFERENCES = {
    "US": ["stripe", "adyen", "paypal"],
    "EU": ["adyen", "stripe", "paypal"],
    "UK": ["stripe", "adyen", "paypal"],
    "CA": ["stripe", "adyen", "paypal"],
    "AU": ["stripe", "adyen", "paypal"],
}
```

## Security Best Practices

### ✅ PCI Compliance
- **Never store raw card data** - Use tokenization
- **Encrypt sensitive data** at rest and in transit
- **Use HTTPS** for all payment-related endpoints
- **Implement access controls** for payment data
- **Regular security audits** and penetration testing

### ✅ Data Protection
```python
# Example of secure data handling
from app.services.payment.security import PCIComplianceManager

pci_manager = PCIComplianceManager()

# Encrypt sensitive data
encrypted_card = pci_manager.encrypt_sensitive_data(card_token)

# Mask for display
masked_card = pci_manager.mask_card_number(card_number)

# Hash for comparison
card_hash = pci_manager.hash_card_data(card_number)
```

### ✅ Webhook Security
```python
# Verify webhook signatures
from app.services.payment.security import WebhookSecurity

# Stripe webhooks
is_valid = WebhookSecurity.verify_stripe_webhook(
    payload=request.body,
    signature=request.headers['Stripe-Signature'],
    webhook_secret=settings.STRIPE_WEBHOOK_SECRET
)
```

## Integration Examples

### Frontend Integration (JavaScript)

```javascript
// Create payment intent
const response = await fetch('/api/v1/payments', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    order_id: 123,
    amount: 99.99,
    currency_code: 'USD',
    payment_method: {
      method_type: 'card',
      card_token: 'pm_xxx' // From Stripe Elements
    },
    customer_email: 'customer@example.com'
  })
});

const { client_secret, payment_id } = await response.json();

// Confirm payment with Stripe
const { error } = await stripe.confirmCardPayment(client_secret, {
  payment_method: {
    card: cardElement,
    billing_details: {
      name: 'John Doe',
    },
  },
});

if (error) {
  // Handle 3D Secure if required
  if (error.code === 'payment_intent_authentication_failure') {
    // Redirect to 3D Secure
  }
} else {
  // Payment successful
  console.log('Payment confirmed!');
}
```

### Server-side Integration (Python)

```python
from app.services.payment.service import PaymentService
from app.schemas.payment import PaymentCreate

# Initialize payment service
payment_service = PaymentService(db)
await payment_service.initialize()

# Create payment
payment_data = PaymentCreate(
    order_id=123,
    amount=Decimal("99.99"),
    currency_code="USD",
    payment_method=PaymentMethodCreate(
        method_type="card",
        card_token="pm_xxx"
    ),
    customer_email="customer@example.com"
)

# Process payment
payment_intent = await payment_service.create_payment(
    payment_data=payment_data,
    customer_ip=request.client.host
)

print(f"Payment created: {payment_intent.payment_id}")
print(f"Client secret: {payment_intent.client_secret}")
```

## Monitoring & Analytics

### Payment Metrics
- **Success rates** by gateway and region
- **Transaction volumes** and amounts
- **Failure patterns** and retry statistics
- **Performance metrics** (response times)

### Health Monitoring
```python
# Check gateway health
health_status = await payment_service._router.get_gateway_metrics()

for gateway, metrics in health_status.items():
    print(f"{gateway}: {'✅' if metrics['is_healthy'] else '❌'}")
    print(f"  Supported methods: {metrics['supported_methods']}")
    print(f"  Test mode: {metrics['test_mode']}")
```

### Alerting
- **Gateway failures** and circuit breaker activation
- **High failure rates** or unusual patterns
- **Security events** and fraud alerts
- **Performance degradation**

## Testing

### Unit Tests
```bash
# Run payment tests
pytest tests/test_payments.py -v

# Run gateway tests
pytest tests/test_gateways.py -v

# Run security tests
pytest tests/test_payment_security.py -v
```

### Integration Tests
```python
# Test payment flow
async def test_payment_flow():
    # Create payment
    payment_intent = await payment_service.create_payment(payment_data)
    
    # Confirm payment
    confirmed_payment = await payment_service.confirm_payment(
        payment_intent.payment_id
    )
    
    # Verify status
    assert confirmed_payment.status == "completed"
    
    # Process refund
    refund = await payment_service.refund_payment(
        payment_intent.payment_id,
        PaymentRefundCreate(amount=50.00)
    )
    
    assert refund.status == "completed"
```

### Test Cards
- **Stripe**: https://stripe.com/docs/testing
- **PayPal**: https://developer.paypal.com/tools/sandbox/
- **Adyen**: https://docs.adyen.com/development-resources/test-cards/

## Deployment

### Production Checklist
- [ ] Set `PAYMENT_TEST_MODE=false`
- [ ] Configure production API keys
- [ ] Set up webhook endpoints with HTTPS
- [ ] Configure encryption keys
- [ ] Set up monitoring and alerting
- [ ] Test all gateway integrations
- [ ] Verify PCI compliance measures
- [ ] Set up backup and disaster recovery

### Scaling Considerations
- **Database optimization** for payment tables
- **Connection pooling** for gateway APIs
- **Caching** for gateway health status
- **Load balancing** across multiple instances
- **Rate limiting** to prevent abuse

## Troubleshooting

### Common Issues

#### Payment Creation Fails
```python
# Check gateway configuration
config = get_gateway_config("stripe", test_mode=True)
if not config.get("api_key"):
    raise ValueError("Stripe API key not configured")
```

#### Webhook Not Processing
```python
# Verify webhook signature
if not WebhookSecurity.verify_stripe_webhook(payload, signature, secret):
    logger.error("Invalid webhook signature")
    return False
```

#### High Failure Rate
```python
# Check circuit breaker status
circuit_breaker = failure_handler.get_circuit_breaker("stripe")
if circuit_breaker.state == "OPEN":
    logger.warning("Stripe circuit breaker is open")
```

### Debug Mode
```python
# Enable debug logging
import logging
logging.getLogger("app.services.payment").setLevel(logging.DEBUG)
```

## Support

### Documentation
- **API Reference**: Check the endpoint documentation
- **Gateway Guides**: Individual gateway documentation
- **Security Guide**: PCI compliance requirements

### Monitoring
- **Health Checks**: `/api/v1/payments/health`
- **Metrics**: `/api/v1/admin/payments/metrics`
- **Logs**: Payment service logs with detailed error information

### Emergency Procedures
1. **Gateway Outage**: Circuit breaker automatically switches gateways
2. **High Failure Rate**: Monitor alerts and check configuration
3. **Security Incident**: Disable affected gateway, rotate keys
4. **Data Breach**: Follow incident response, notify authorities

---

This payment system is designed for production use with enterprise-level reliability, security, and scalability. Always test thoroughly in sandbox environments before deploying to production.
