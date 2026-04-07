# Payment API Cheat Sheet - Quick Reference

## 🚀 Base URLs
```
Development: http://localhost:8000/api/v1
Production:  https://yourstore.com/api/v1
```

## 📡 Core Endpoints

### Create Payment Intent
```http
POST /payments
```
**Body:**
```json
{
  "order_id": 123,
  "amount": 99.99,
  "currency_code": "USD",
  "payment_method": { "method_type": "card" },
  "customer_email": "user@example.com",
  "preferred_gateway": "stripe" // optional
}
```
**Response:**
```json
{
  "client_secret": "pi_xxx_secret_xxx",
  "payment_id": 456,
  "gateway": "stripe",
  "amount": 99.99,
  "currency_code": "USD",
  "status": "pending"
}
```

### Confirm Payment
```http
POST /payments/{payment_id}/confirm
```
**Body:**
```json
{
  "payment_method": {
    "method_type": "card",
    "card_last4": "4242",
    "card_brand": "visa"
  }
}
```

### Get Payment Status
```http
GET /payments/{payment_id}
```

### Cancel Payment
```http
POST /payments/{payment_id}/cancel
```

### Process Refund
```http
POST /payments/{payment_id}/refunds
```
**Body:**
```json
{
  "amount": 50.00,
  "reason": "Customer requested refund"
}
```

### Get Supported Methods
```http
GET /payments/methods
```

### Gateway Health Check
```http
GET /payments/health
```

## 🎯 Response Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process response |
| 201 | Created | Payment intent created |
| 400 | Bad Request | Fix request body |
| 401 | Unauthorized | Check auth token |
| 404 | Not Found | Invalid payment_id |
| 429 | Rate Limited | Implement retry |
| 500 | Server Error | Retry with backoff |

## 💳 Gateway-Specific

### Stripe
- **Client Secret**: Used with `stripe.confirmCardPayment()`
- **3D Secure**: Handle `requires_action` status
- **Test Cards**: `4242424242424242` (success), `4000000000000002` (decline)

### PayPal
- **Redirect**: User redirected to PayPal, then returns
- **Return URL**: Configure in PayPal dashboard
- **Sandbox**: Use sandbox credentials for testing

### Adyen
- **Payment Data**: Used with Adyen Web components
- **Actions**: Handle 3D Secure and other verifications
- **Test Environment**: Use test environment for development

## 🔧 JavaScript Examples

### Fetch Wrapper
```javascript
const apiCall = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = localStorage.getItem('authToken');
  
  const config = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(url, config);
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || 'API call failed');
  }

  return data;
};
```

### Create Payment
```javascript
const createPayment = async (orderData, customerEmail) => {
  try {
    const payment = await apiCall('/payments', {
      method: 'POST',
      body: JSON.stringify({
        order_id: orderData.id,
        amount: orderData.total,
        currency_code: orderData.currency,
        payment_method: { method_type: 'card' },
        customer_email: customerEmail,
      }),
    });

    return payment;
  } catch (error) {
    console.error('Payment creation failed:', error);
    throw error;
  }
};
```

### Stripe Payment
```javascript
const handleStripePayment = async (clientSecret) => {
  const { error, paymentIntent } = await stripe.confirmCardPayment(clientSecret, {
    payment_method: {
      card: cardElement,
      billing_details: { name: 'John Doe' },
    },
  });

  if (error) {
    throw error;
  }

  return paymentIntent;
};
```

## 🚨 Error Handling

### Common Errors
```javascript
const handlePaymentError = (error, gateway) => {
  const errorMap = {
    'card_declined': 'Your card was declined. Please try another card.',
    'insufficient_funds': 'Insufficient funds. Please try another payment method.',
    'processing_error': 'Payment processing failed. Please try again.',
    'network_error': 'Network error. Please check your connection.',
  };

  return errorMap[error.type] || 'Payment failed. Please try again.';
};
```

### Retry Logic
```javascript
const retryPayment = async (paymentId, maxRetries = 3) => {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const result = await apiCall(`/payments/${paymentId}/confirm`, {
        method: 'POST',
      });
      return result;
    } catch (error) {
      if (attempt === maxRetries) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
    }
  }
};
```

## 📱 Mobile Considerations

### Responsive Design
```css
.payment-form {
  max-width: 100%;
  padding: 1rem;
}

@media (max-width: 768px) {
  .payment-form {
    padding: 0.5rem;
  }
  
  .gateway-selector select {
    font-size: 16px; /* Prevent zoom on iOS */
  }
}
```

### Touch Optimization
```javascript
// Larger touch targets for mobile
const buttonStyles = {
  padding: '16px 24px',
  fontSize: '16px',
  minHeight: '48px',
};
```

## 🔍 Testing

### Mock Responses
```javascript
const mockPaymentResponse = {
  client_secret: 'pi_test_secret',
  payment_id: 123,
  gateway: 'stripe',
  status: 'pending',
  amount: 99.99,
  currency_code: 'USD',
};
```

### Test Scenarios
- ✅ Successful payment creation
- ✅ Payment confirmation
- ✅ Card declined
- ✅ Network error handling
- ✅ 3D Secure flow
- ✅ Gateway fallback

## 📊 Monitoring

### Events to Track
```javascript
// Payment events
track('Payment Started', { gateway: 'stripe', amount: 99.99 });
track('Payment Completed', { payment_id: 123, gateway: 'stripe' });
track('Payment Failed', { error: 'card_declined', gateway: 'stripe' });
track('Payment Method Changed', { from: 'stripe', to: 'paypal' });
```

### Performance Metrics
- Payment creation time
- Confirmation response time
- Gateway health status
- Error rates by gateway

## 🚀 Quick Start Checklist

### Development Setup
- [ ] Copy `.env.example.payment` to `.env`
- [ ] Set test API keys
- [ ] Install payment SDKs (`@stripe/stripe-js`, etc.)
- [ ] Configure API base URL
- [ ] Set up authentication

### Integration Steps
1. Create payment intent → Get `client_secret`
2. Initialize payment form → Collect payment details
3. Process payment → Handle success/failure
4. Update UI → Show confirmation/error
5. Handle webhooks → Process async events

### Production Checklist
- [ ] Use production API keys
- [ ] Enable HTTPS
- [ ] Set up error monitoring
- [ ] Test all payment flows
- [ ] Configure analytics
- [ ] Set up webhook endpoints

---

**Need help?** Check the full documentation at `docs/frontend_integration.md` or contact the backend team.
