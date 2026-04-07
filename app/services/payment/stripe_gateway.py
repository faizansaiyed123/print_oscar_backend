"""Stripe payment gateway implementation."""

import json
from decimal import Decimal
from typing import Any, Dict, List, Optional

import stripe
from stripe.error import StripeError, APIConnectionError, CardError

from app.models.payment import PaymentMethod, PaymentStatus
from app.schemas.payment import (
    PaymentCreate,
    PaymentMethodCreate,
    PaymentRefundCreate,
    PaymentVerificationRequest,
    PaymentVerificationResponse,
)
from app.services.payment.gateway import GatewayResponse, PaymentGateway


class StripeGateway(PaymentGateway):
    """Stripe payment gateway implementation."""
    
    def __init__(self, config: Dict[str, Any], test_mode: bool = True):
        super().__init__(config, test_mode)
        stripe.api_key = config.get("api_key")
        self.webhook_secret = config.get("webhook_secret")
        self.max_retries = config.get("max_retries", 3)
    
    async def create_payment_intent(
        self, 
        payment_data: PaymentCreate,
        order_id: int
    ) -> GatewayResponse:
        """Create a Stripe payment intent."""
        try:
            # Convert amount to cents for Stripe
            amount_cents = int(payment_data.amount * 100)
            
            # Create payment intent
            intent_params = {
                "amount": amount_cents,
                "currency": payment_data.currency_code.lower(),
                "metadata": {
                    "order_id": str(order_id),
                    "payment_id": str(payment_data.payment_metadata.get("payment_id", "")),
                },
                "automatic_payment_methods": {"enabled": True},
                "receipt_email": payment_data.customer_email,
            }
            
            # Add payment method if provided
            if payment_data.payment_method.card_token:
                intent_params["payment_method"] = payment_data.payment_method.card_token
                intent_params["confirm"] = True
                intent_params["confirmation_method"] = "manual"
            
            # Create the intent
            intent = stripe.PaymentIntent.create(**intent_params)
            
            # Calculate fees (Stripe typically 2.9% + $0.30)
            fee_amount = self.calculate_fee(payment_data.amount)
            
            return GatewayResponse(
                success=True,
                gateway_payment_id=intent.id,
                client_secret=intent.client_secret,
                status=self._map_stripe_status(intent.status),
                gateway_response=dict(intent),
                fee_amount=fee_amount,
                requires_action=intent.status == "requires_action",
                next_action={
                    "type": "stripe_verification",
                    "client_secret": intent.client_secret,
                    "payment_method": intent.payment_method,
                } if intent.status == "requires_action" else None,
            )
            
        except StripeError as e:
            return GatewayResponse(
                success=False,
                error_message=str(e),
                status=PaymentStatus.FAILED,
                gateway_response={"error": str(e)}
            )
        except Exception as e:
            return GatewayResponse(
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                status=PaymentStatus.FAILED
            )
    
    async def confirm_payment(
        self,
        gateway_payment_id: str,
        payment_method_data: Optional[PaymentMethodCreate] = None
    ) -> GatewayResponse:
        """Confirm a Stripe payment."""
        try:
            intent = stripe.PaymentIntent.confirm(gateway_payment_id)
            
            return GatewayResponse(
                success=True,
                gateway_payment_id=intent.id,
                status=self._map_stripe_status(intent.status),
                gateway_response=dict(intent),
            )
            
        except StripeError as e:
            return GatewayResponse(
                success=False,
                error_message=str(e),
                status=PaymentStatus.FAILED,
                gateway_response={"error": str(e)}
            )
    
    async def cancel_payment(self, gateway_payment_id: str) -> GatewayResponse:
        """Cancel a Stripe payment."""
        try:
            intent = stripe.PaymentIntent.cancel(gateway_payment_id)
            
            return GatewayResponse(
                success=True,
                gateway_payment_id=intent.id,
                status=self._map_stripe_status(intent.status),
                gateway_response=dict(intent),
            )
            
        except StripeError as e:
            return GatewayResponse(
                success=False,
                error_message=str(e),
                status=PaymentStatus.FAILED,
                gateway_response={"error": str(e)}
            )
    
    async def refund_payment(
        self,
        gateway_payment_id: str,
        refund_data: PaymentRefundCreate
    ) -> GatewayResponse:
        """Process a Stripe refund."""
        try:
            # Convert amount to cents
            amount_cents = int(refund_data.amount * 100)
            
            refund = stripe.Refund.create(
                payment_intent=gateway_payment_id,
                amount=amount_cents,
                reason=refund_data.reason or "requested_by_customer"
            )
            
            return GatewayResponse(
                success=True,
                gateway_payment_id=refund.id,
                status=self._map_refund_status(refund.status),
                gateway_response=dict(refund),
            )
            
        except StripeError as e:
            return GatewayResponse(
                success=False,
                error_message=str(e),
                status=PaymentStatus.FAILED,
                gateway_response={"error": str(e)}
            )
    
    async def retrieve_payment(self, gateway_payment_id: str) -> GatewayResponse:
        """Retrieve payment details from Stripe."""
        try:
            intent = stripe.PaymentIntent.retrieve(gateway_payment_id)
            
            return GatewayResponse(
                success=True,
                gateway_payment_id=intent.id,
                status=self._map_stripe_status(intent.status),
                gateway_response=dict(intent),
            )
            
        except StripeError as e:
            return GatewayResponse(
                success=False,
                error_message=str(e),
                status=PaymentStatus.FAILED,
                gateway_response={"error": str(e)}
            )
    
    async def verify_payment(
        self,
        verification_request: PaymentVerificationRequest
    ) -> PaymentVerificationResponse:
        """Verify payment with 3D Secure or other methods."""
        try:
            intent = stripe.PaymentIntent.retrieve(
                verification_request.verification_data.get("payment_intent_id")
            )
            
            if intent.status == "succeeded":
                return PaymentVerificationResponse(
                    payment_id=verification_request.payment_id,
                    status="completed",
                    is_verified=True,
                    verification_method=verification_request.verification_method,
                )
            elif intent.status == "requires_action":
                return PaymentVerificationResponse(
                    payment_id=verification_request.payment_id,
                    status="pending",
                    is_verified=False,
                    verification_method=verification_request.verification_method,
                    next_action={
                        "type": "3ds_challenge",
                        "client_secret": intent.client_secret,
                        "payment_method": intent.payment_method,
                    }
                )
            else:
                return PaymentVerificationResponse(
                    payment_id=verification_request.payment_id,
                    status="failed",
                    is_verified=False,
                    verification_method=verification_request.verification_method,
                    error_message=f"Payment failed: {intent.last_payment_error}",
                )
                
        except StripeError as e:
            return PaymentVerificationResponse(
                payment_id=verification_request.payment_id,
                status="failed",
                is_verified=False,
                verification_method=verification_request.verification_method,
                error_message=str(e),
            )
    
    async def create_payment_method(
        self,
        method_data: PaymentMethodCreate,
        customer_email: str
    ) -> GatewayResponse:
        """Create a payment method for future use."""
        try:
            # Create or get customer
            customer = self._get_or_create_customer(customer_email)
            
            # Create payment method
            payment_method_params = {
                "type": "card",
                "card": {
                    "token": method_data.card_token,
                } if method_data.card_token else {
                    "number": method_data.card_last4,
                    "exp_month": method_data.card_exp_month,
                    "exp_year": method_data.card_exp_year,
                },
                "billing": method_data.billing_address,
            }
            
            payment_method = stripe.PaymentMethod.create(**payment_method_params)
            
            # Attach to customer
            stripe.PaymentMethod.attach(
                payment_method.id,
                customer=customer.id
            )
            
            return GatewayResponse(
                success=True,
                gateway_payment_id=payment_method.id,
                status=PaymentStatus.COMPLETED,
                gateway_response=dict(payment_method),
            )
            
        except StripeError as e:
            return GatewayResponse(
                success=False,
                error_message=str(e),
                status=PaymentStatus.FAILED,
                gateway_response={"error": str(e)}
            )
    
    async def health_check(self) -> bool:
        """Check if Stripe is accessible."""
        try:
            # Make a simple API call to check connectivity
            stripe.Account.retrieve()
            return True
        except (APIConnectionError, StripeError):
            return False
    
    def get_supported_payment_methods(self) -> List[PaymentMethod]:
        """Get supported payment methods for Stripe."""
        return [
            PaymentMethod.CARD,
            PaymentMethod.DIGITAL_WALLET,  # Apple Pay, Google Pay
        ]
    
    def get_supported_currencies(self) -> List[str]:
        """Get supported currencies for Stripe."""
        # Stripe supports most major currencies
        return [
            "USD", "EUR", "GBP", "CAD", "AUD", "CHF", "SEK", "NOK", "DKK",
            "PLN", "CZK", "HUF", "RON", "BGN", "HRK", "RUB", "UAH",
            "MXN", "BRL", "ARS", "CLP", "COP", "PEN", "UYU",
            "JPY", "SGD", "HKD", "CNY", "INR", "THB", "MYR", "IDR",
            "PHP", "VND", "KRW", "TWD", "NZD"
        ]
    
    def calculate_fee(self, amount: Decimal) -> Decimal:
        """Calculate Stripe fees (2.9% + $0.30 for US cards)."""
        percentage_fee = amount * Decimal("0.029")  # 2.9%
        fixed_fee = Decimal("0.30")
        return percentage_fee + fixed_fee
    
    def _get_or_create_customer(self, email: str) -> Any:
        """Get existing customer or create new one."""
        try:
            # Try to find existing customer
            customers = stripe.Customer.list(email=email, limit=1)
            if customers.data:
                return customers.data[0]
        except StripeError:
            pass
        
        # Create new customer
        return stripe.Customer.create(email=email)
    
    def _map_stripe_status(self, stripe_status: str) -> PaymentStatus:
        """Map Stripe status to our PaymentStatus enum."""
        status_mapping = {
            "requires_payment_method": PaymentStatus.PENDING,
            "requires_confirmation": PaymentStatus.PENDING,
            "requires_action": PaymentStatus.PENDING,
            "processing": PaymentStatus.PROCESSING,
            "succeeded": PaymentStatus.COMPLETED,
            "canceled": PaymentStatus.CANCELLED,
        }
        return status_mapping.get(stripe_status, PaymentStatus.FAILED)
    
    def _map_refund_status(self, refund_status: str) -> PaymentStatus:
        """Map Stripe refund status to our PaymentStatus enum."""
        status_mapping = {
            "pending": PaymentStatus.PENDING,
            "succeeded": PaymentStatus.COMPLETED,
            "failed": PaymentStatus.FAILED,
            "canceled": PaymentStatus.CANCELLED,
        }
        return status_mapping.get(refund_status, PaymentStatus.FAILED)
