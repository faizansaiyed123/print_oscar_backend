# Frontend Integration Guide - Payment System

This guide provides everything your frontend team needs to integrate with the new multi-payment system.

## 🚀 Quick Start

### 1. Base URL Configuration
```javascript
// config/api.js
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://yourstore.com/api/v1' 
  : 'http://localhost:8000/api/v1';

export const API_ENDPOINTS = {
  payments: `${API_BASE_URL}/payments`,
  webhooks: `${API_BASE_URL}/webhooks`,
  auth: `${API_BASE_URL}/auth`,
};
```

### 2. Payment Flow Overview
```
1. Create Payment Intent → Get client_secret
2. Initialize Payment Form → Collect payment details
3. Confirm Payment → Process payment
4. Handle Verification → 3D Secure if required
5. Complete → Update UI with success/error
```

## 📡 API Endpoints

### Create Payment Intent
```http
POST /api/v1/payments
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "order_id": 123,
  "amount": 99.99,
  "currency_code": "USD",
  "payment_method": {
    "method_type": "card"
  },
  "customer_email": "customer@example.com",
  "preferred_gateway": "stripe"
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
  "status": "pending",
  "expires_at": "2024-01-01T12:00:00Z"
}
```

### Confirm Payment
```http
POST /api/v1/payments/{payment_id}/confirm
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "payment_method": {
    "method_type": "card",
    "card_last4": "4242",
    "card_brand": "visa"
  }
}
```

### Get Payment Details
```http
GET /api/v1/payments/{payment_id}
Authorization: Bearer {jwt_token}
```

### Get Supported Payment Methods
```http
GET /api/v1/payments/methods
```

## 💳 Payment Gateway Integration

### Stripe Integration

#### 1. Install Stripe.js
```bash
npm install @stripe/stripe-js
```

#### 2. Stripe Payment Component
```jsx
// components/StripePayment.jsx
import { loadStripe } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';

const stripePromise = loadStripe('pk_test_xxx'); // Use publishable key from config

const StripePaymentForm = ({ clientSecret, onSuccess, onError }) => {
  const stripe = useStripe();
  const elements = useElements();

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!stripe || !elements) {
      return;
    }

    const cardElement = elements.getElement(CardElement);

    const { error, paymentIntent } = await stripe.confirmCardPayment(clientSecret, {
      payment_method: {
        card: cardElement,
        billing_details: {
          name: 'John Doe',
          email: 'customer@example.com',
        },
      },
    });

    if (error) {
      if (error.type === 'card_error' || error.type === 'validation_error') {
        onError(error.message);
      } else {
        onError('An unexpected error occurred.');
      }
    } else if (paymentIntent.status === 'succeeded') {
      onSuccess(paymentIntent);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <CardElement
        options={{
          style: {
            base: {
              fontSize: '16px',
              color: '#424770',
              '::placeholder': {
                color: '#aab7c4',
              },
            },
          },
        }}
      />
      <button type="submit" disabled={!stripe}>
        Pay Now
      </button>
    </form>
  );
};

const StripePayment = ({ paymentData }) => {
  return (
    <Elements stripe={stripePromise}>
      <StripePaymentForm
        clientSecret={paymentData.client_secret}
        onSuccess={(result) => console.log('Payment successful:', result)}
        onError={(error) => console.error('Payment error:', error)}
      />
    </Elements>
  );
};

export default StripePayment;
```

#### 3. 3D Secure Handling
```jsx
// Handle 3D Secure redirects
const handlePayment = async (clientSecret) => {
  const { error, paymentIntent } = await stripe.confirmCardPayment(clientSecret, {
    payment_method: {
      card: cardElement,
      billing_details: { name: customerName },
    },
    return_url: `${window.location.origin}/payment/complete`,
  });

  if (error) {
    // Handle error
  } else if (paymentIntent.status === 'requires_action') {
    // 3D Secure required - Stripe will handle redirect
    stripe.handleCardAction(paymentIntent.client_secret);
  } else if (paymentIntent.status === 'succeeded') {
    // Payment successful
    onPaymentSuccess(paymentIntent);
  }
};
```

### PayPal Integration

#### 1. PayPal SDK Component
```jsx
// components/PayPalPayment.jsx
import { useEffect, useState } from 'react';

const PayPalPayment = ({ paymentData, onSuccess, onError }) => {
  const [isSdkLoaded, setIsSdkLoaded] = useState(false);

  useEffect(() => {
    // Load PayPal SDK
    const script = document.createElement('script');
    script.src = 'https://www.paypal.com/sdk/js?client-id=YOUR_CLIENT_ID&currency=USD';
    script.onload = () => setIsSdkLoaded(true);
    document.body.appendChild(script);

    return () => {
      document.body.removeChild(script);
    };
  }, []);

  useEffect(() => {
    if (isSdkLoaded && window.paypal) {
      window.paypal.Buttons({
        createOrder: async (data, actions) => {
          // Payment intent should already be created
          // Return the PayPal order ID from backend
          return paymentData.gateway_payment_id;
        },
        onApprove: async (data, actions) => {
          try {
            // Confirm payment with backend
            const response = await fetch(`/api/v1/payments/${paymentData.payment_id}/confirm`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAuthToken()}`,
              },
            });

            const result = await response.json();
            
            if (result.status === 'completed') {
              onSuccess(result);
            } else {
              onError('Payment confirmation failed');
            }
          } catch (error) {
            onError(error.message);
          }
        },
        onError: (err) => {
          onError(err.message);
        },
      }).render('#paypal-button-container');
    }
  }, [isSdkLoaded, paymentData]);

  return <div id="paypal-button-container"></div>;
};

export default PayPalPayment;
```

#### 2. PayPal Return Handling
```jsx
// components/PayPalReturn.jsx
import { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

const PayPalReturn = () => {
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const paymentId = params.get('paymentId');
    const payerId = params.get('PayerID');
    const orderId = params.get('order_id');

    if (paymentId && payerId) {
      // Confirm payment with backend
      confirmPayPalPayment(orderId, { paymentId, payerId });
    }
  }, [location]);

  const confirmPayPalPayment = async (orderId, paypalData) => {
    try {
      const response = await fetch(`/api/v1/payments/confirm-paypal`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAuthToken()}`,
        },
        body: JSON.stringify({
          order_id: orderId,
          paypal_data: paypalData,
        }),
      });

      const result = await response.json();
      
      if (result.success) {
        navigate('/payment/success');
      } else {
        navigate('/payment/error', { state: { error: result.error } });
      }
    } catch (error) {
      navigate('/payment/error', { state: { error: error.message } });
    }
  };

  return <div>Processing PayPal payment...</div>;
};
```

### Adyen Integration

#### 1. Adyen Web Component
```jsx
// components/AdyenPayment.jsx
import { useEffect, useState } from 'react';
import { loadAdyen } from '@adyen/adyen-web';

const AdyenPayment = ({ paymentData, onSuccess, onError }) => {
  const [adyenCheckout, setAdyenCheckout] = useState(null);

  useEffect(() => {
    const initializeAdyen = async () => {
      try {
        const Adyen = await loadAdyen({
          environment: 'test', // or 'live'
          clientKey: 'YOUR_CLIENT_KEY',
        });

        const checkout = await Adyen({
          paymentMethodsResponse: paymentData.payment_methods,
          clientKey: 'YOUR_CLIENT_KEY',
          locale: 'en-US',
          environment: 'test',
          paymentMethodsConfiguration: {
            card: {
              hasHolderName: true,
              holderNameRequired: true,
              enableStoreDetails: false,
            },
          },
        });

        setAdyenCheckout(checkout);
      } catch (error) {
        onError('Failed to load Adyen');
      }
    };

    initializeAdyen();
  }, [paymentData]);

  useEffect(() => {
    if (adyenCheckout) {
      adyenCheckout.create('card').mount('#adyen-card-container');
    }
  }, [adyenCheckout]);

  const handlePayment = async () => {
    try {
      const result = await adyenCheckout.submitPayment();

      if (result.action) {
        // Handle 3D Secure or other actions
        adyenCheckout.handleAction(result.action);
      } else {
        // Payment successful
        onSuccess(result);
      }
    } catch (error) {
      onError(error.message);
    }
  };

  return (
    <div>
      <div id="adyen-card-container"></div>
      <button onClick={handlePayment}>Pay Now</button>
    </div>
  );
};

export default AdyenPayment;
```

## 🔄 Payment Flow Integration

### Complete Payment Component
```jsx
// components/PaymentFlow.jsx
import { useState, useEffect } from 'react';
import StripePayment from './StripePayment';
import PayPalPayment from './PayPalPayment';
import AdyenPayment from './AdyenPayment';

const PaymentFlow = ({ orderData, customerData }) => {
  const [paymentData, setPaymentData] = useState(null);
  const [selectedGateway, setSelectedGateway] = useState('stripe');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Create payment intent
  const createPaymentIntent = async (gateway) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/payments', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAuthToken()}`,
        },
        body: JSON.stringify({
          order_id: orderData.id,
          amount: orderData.total,
          currency_code: orderData.currency,
          payment_method: {
            method_type: 'card',
          },
          customer_email: customerData.email,
          preferred_gateway: gateway,
        }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'Failed to create payment');
      }

      setPaymentData(result);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  // Handle payment success
  const handlePaymentSuccess = async (result) => {
    try {
      // Confirm payment with backend
      const response = await fetch(`/api/v1/payments/${paymentData.payment_id}/confirm`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAuthToken()}`,
        },
      });

      const confirmation = await response.json();

      if (confirmation.status === 'completed') {
        // Redirect to success page
        window.location.href = '/order/success';
      } else {
        setError('Payment confirmation failed');
      }
    } catch (error) {
      setError(error.message);
    }
  };

  // Get supported payment methods
  useEffect(() => {
    const getPaymentMethods = async () => {
      try {
        const response = await fetch('/api/v1/payments/methods');
        const methods = await response.json();
        
        // Select first available gateway
        if (methods.payment_methods.length > 0) {
          setSelectedGateway(methods.payment_methods[0].gateway);
        }
      } catch (error) {
        console.error('Failed to get payment methods:', error);
      }
    };

    getPaymentMethods();
  }, []);

  // Create payment intent when gateway is selected
  useEffect(() => {
    if (selectedGateway && !paymentData) {
      createPaymentIntent(selectedGateway);
    }
  }, [selectedGateway]);

  if (loading) {
    return <div>Initializing payment...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!paymentData) {
    return <div>Loading payment options...</div>;
  }

  return (
    <div>
      <h2>Complete Your Payment</h2>
      
      {/* Gateway Selection */}
      <div className="gateway-selector">
        <label>Select Payment Method:</label>
        <select 
          value={selectedGateway} 
          onChange={(e) => setSelectedGateway(e.target.value)}
        >
          <option value="stripe">Credit Card (Stripe)</option>
          <option value="paypal">PayPal</option>
          <option value="adyen">Adyen</option>
        </select>
      </div>

      {/* Payment Form */}
      <div className="payment-form">
        {selectedGateway === 'stripe' && (
          <StripePayment
            clientSecret={paymentData.client_secret}
            onSuccess={handlePaymentSuccess}
            onError={setError}
          />
        )}
        
        {selectedGateway === 'paypal' && (
          <PayPalPayment
            paymentData={paymentData}
            onSuccess={handlePaymentSuccess}
            onError={setError}
          />
        )}
        
        {selectedGateway === 'adyen' && (
          <AdyenPayment
            paymentData={paymentData}
            onSuccess={handlePaymentSuccess}
            onError={setError}
          />
        )}
      </div>

      <div className="order-summary">
        <h3>Order Summary</h3>
        <p>Total: ${orderData.total} {orderData.currency}</p>
      </div>
    </div>
  );
};

export default PaymentFlow;
```

## 🛡️ Error Handling

### Error Types and Handling
```jsx
// utils/paymentErrors.js
export const PAYMENT_ERRORS = {
  CARD_DECLINED: 'card_declined',
  INSUFFICIENT_FUNDS: 'insufficient_funds',
  PROCESSING_ERROR: 'processing_error',
  NETWORK_ERROR: 'network_error',
  VERIFICATION_REQUIRED: 'verification_required',
};

export const getPaymentErrorMessage = (error, gateway) => {
  const errorMessages = {
    stripe: {
      'card_declined': 'Your card was declined. Please try another card.',
      'insufficient_funds': 'Insufficient funds. Please try another payment method.',
      'processing_error': 'Payment processing failed. Please try again.',
      'incorrect_number': 'Card number is incorrect.',
      'invalid_expiry_month': 'Expiry month is invalid.',
      'invalid_expiry_year': 'Expiry year is invalid.',
      'invalid_cvc': 'CVC is invalid.',
    },
    paypal: {
      'payment_declined': 'Payment was declined. Please try another payment method.',
      'timeout': 'Payment timed out. Please try again.',
    },
    adyen: {
      'Declined': 'Payment was declined. Please try another payment method.',
      'Refused': 'Payment was refused by the bank.',
      'Cancelled': 'Payment was cancelled.',
    },
  };

  return errorMessages[gateway]?.[error.type] || 'Payment failed. Please try again.';
};
```

### Error Boundary Component
```jsx
// components/PaymentErrorBoundary.jsx
import React from 'react';

class PaymentErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Payment Error:', error, errorInfo);
    // Log to error tracking service
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="payment-error">
          <h2>Something went wrong with the payment</h2>
          <p>We're sorry, but there was an error processing your payment.</p>
          <button onClick={() => this.setState({ hasError: false, error: null })}>
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default PaymentErrorBoundary;
```

## 📱 Mobile Optimization

### Responsive Payment Forms
```css
/* styles/payment.css */
.payment-form {
  max-width: 100%;
  margin: 0 auto;
}

@media (max-width: 768px) {
  .payment-form {
    padding: 1rem;
  }
  
  .gateway-selector select {
    width: 100%;
    padding: 12px;
    font-size: 16px; /* Prevent zoom on iOS */
  }
  
  .card-element {
    padding: 12px;
    border: 1px solid #ccc;
    border-radius: 4px;
  }
}

/* Loading states */
.payment-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
```

## 🔧 Configuration Management

### Environment Configuration
```javascript
// config/payment.js
const PAYMENT_CONFIG = {
  stripe: {
    publishableKey: process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY,
    testMode: process.env.NODE_ENV === 'development',
  },
  paypal: {
    clientId: process.env.REACT_APP_PAYPAL_CLIENT_ID,
    currency: 'USD',
    environment: process.env.NODE_ENV === 'development' ? 'sandbox' : 'production',
  },
  adyen: {
    clientKey: process.env.REACT_APP_ADYEN_CLIENT_KEY,
    environment: process.env.NODE_ENV === 'development' ? 'test' : 'live',
  },
  api: {
    baseUrl: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1',
    timeout: 30000,
  },
};

export default PAYMENT_CONFIG;
```

## 🧪 Testing

### Mock Payment Service
```javascript
// __tests__/mockPaymentService.js
export const mockPaymentService = {
  createPaymentIntent: jest.fn().mockResolvedValue({
    client_secret: 'pi_test_secret',
    payment_id: 123,
    gateway: 'stripe',
    status: 'pending',
  }),
  
  confirmPayment: jest.fn().mockResolvedValue({
    status: 'completed',
    id: 123,
  }),
  
  getPaymentMethods: jest.fn().mockResolvedValue({
    payment_methods: [
      { gateway: 'stripe', methods: ['card'] },
      { gateway: 'paypal', methods: ['paypal'] },
    ],
  }),
};
```

### Component Testing Example
```jsx
// __tests__/PaymentFlow.test.jsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import PaymentFlow from '../components/PaymentFlow';
import { mockPaymentService } from './mockPaymentService';

jest.mock('../services/paymentService', () => mockPaymentService);

describe('PaymentFlow', () => {
  test('creates payment intent on mount', async () => {
    render(
      <PaymentFlow 
        orderData={{ id: 1, total: 99.99, currency: 'USD' }}
        customerData={{ email: 'test@example.com' }}
      />
    );

    await waitFor(() => {
      expect(mockPaymentService.createPaymentIntent).toHaveBeenCalled();
    });
  });

  test('handles payment success', async () => {
    render(
      <PaymentFlow 
        orderData={{ id: 1, total: 99.99, currency: 'USD' }}
        customerData={{ email: 'test@example.com' }}
      />
    );

    // Simulate successful payment
    const payButton = screen.getByText('Pay Now');
    fireEvent.click(payButton);

    await waitFor(() => {
      expect(window.location.href).toBe('/order/success');
    });
  });
});
```

## 📊 Analytics & Tracking

### Payment Events
```javascript
// utils/paymentAnalytics.js
export const trackPaymentEvent = (eventName, properties) => {
  // Track with your analytics service
  if (window.analytics) {
    window.analytics.track(eventName, properties);
  }
};

export const paymentEvents = {
  PAYMENT_INITIATED: 'Payment Initiated',
  PAYMENT_METHOD_SELECTED: 'Payment Method Selected',
  PAYMENT_COMPLETED: 'Payment Completed',
  PAYMENT_FAILED: 'Payment Failed',
  PAYMENT_CANCELLED: 'Payment Cancelled',
};

// Usage in components
const handlePaymentSuccess = (result) => {
  trackPaymentEvent(paymentEvents.PAYMENT_COMPLETED, {
    gateway: selectedGateway,
    amount: orderData.total,
    currency: orderData.currency,
    payment_id: result.id,
  });
  
  // Continue with success flow
};
```

## 🚀 Deployment Checklist

### Frontend Deployment
- [ ] Update environment variables with production keys
- [ ] Enable HTTPS for all payment-related pages
- [ ] Test payment flows in production environment
- [ ] Set up error monitoring and logging
- [ ] Configure analytics and tracking
- [ ] Test mobile responsiveness
- [ ] Verify accessibility compliance

### Security Considerations
- [ ] Never expose secret keys in frontend code
- [ ] Use HTTPS for all API calls
- [ ] Validate payment amounts on frontend and backend
- [ ] Implement proper error handling
- [ ] Add CSRF protection for payment forms
- [ ] Log payment events for audit trails

This guide provides everything your frontend team needs to successfully integrate with the payment system. The modular design allows for easy testing, maintenance, and future enhancements.
