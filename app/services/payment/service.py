"""Main payment service orchestrating all payment operations."""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import (
    Payment,
    PaymentGateway,
    PaymentMethod,
    PaymentMethodDetails,
    PaymentRefund,
    PaymentStatus,
    PaymentTransaction,
    PaymentType,
)
from app.repositories.payment import PaymentRepository
from app.schemas.payment import (
    PaymentCreate,
    PaymentIntentResponse,
    PaymentMethodCreate,
    PaymentRefundCreate,
    PaymentRefundResponse,
    PaymentResponse,
    PaymentVerificationRequest,
    PaymentVerificationResponse,
    PaymentWebhookPayload,
)
from app.services.payment.adyen_gateway import AdyenGateway
from app.services.payment.gateway import GatewayResponse
# from app.services.payment.paypal_gateway import PayPalGateway  # Temporarily disabled
from app.services.payment.router import GeographyRouter
# from app.services.payment.stripe_gateway import StripeGateway  # Temporarily disabled

logger = logging.getLogger(__name__)


class PaymentService:
    """Main payment service orchestrating payment operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = PaymentRepository(db)
        self._gateways = {}
        self._router = None
        self._max_retries = 3
        self._retry_delay = timedelta(seconds=2)
    
    async def initialize(self):
        """Initialize payment gateways and router."""
        await self._load_gateway_configs()
        await self._initialize_gateways()
        self._router = GeographyRouter(self._gateways)
    
    async def create_payment(
        self, 
        payment_data: PaymentCreate,
        customer_ip: Optional[str] = None
    ) -> PaymentIntentResponse:
        """Create a new payment with intelligent gateway selection."""
        try:
            # Validate order exists and amount matches
            await self._validate_order(payment_data.order_id, payment_data.amount)
            
            # Select optimal gateway
            gateway_name, fallback_gateways = await self._router.select_gateway(
                amount=payment_data.amount,
                currency_code=payment_data.currency_code,
                payment_method=PaymentMethod(payment_data.payment_method.method_type),
                preferred_gateway=payment_data.preferred_gateway,
            )
            
            gateway = self._gateways[gateway_name]
            
            # Create payment record
            payment = Payment(
                order_id=payment_data.order_id,
                payment_gateway=PaymentGateway(gateway_name),
                status=PaymentStatus.PENDING,
                payment_type=PaymentType.ONE_TIME,
                payment_method=PaymentMethod(payment_data.payment_method.method_type),
                amount=payment_data.amount,
                currency_code=payment_data.currency_code,
                customer_email=payment_data.customer_email,
                customer_ip=customer_ip,
                payment_metadata=payment_data.payment_metadata,
            )
            
            payment = await self.repository.create_payment(payment)
            
            # Create payment intent with gateway
            gateway_response = await gateway.create_payment_intent(
                payment_data, payment_data.order_id
            )
            
            # Update payment with gateway response
            if gateway_response.success:
                payment.gateway_payment_id = gateway_response.gateway_payment_id
                payment.status = gateway_response.status
                payment.fee_amount = gateway_response.fee_amount or Decimal("0.00")
                payment.gateway_response = gateway_response.gateway_response
                
                # Create payment method details if provided
                if payment_data.payment_method.method_type == "card":
                    method_details = PaymentMethodDetails(
                        payment_id=payment.id,
                        method_type=PaymentMethod.CARD,
                        card_last4=payment_data.payment_method.card_last4,
                        card_brand=payment_data.payment_method.card_brand,
                        card_exp_month=payment_data.payment_method.card_exp_month,
                        card_exp_year=payment_data.payment_method.card_exp_year,
                    )
                    await self.repository.create_payment_method_details(method_details)
                
                # Create initial transaction record
                transaction = PaymentTransaction(
                    payment_id=payment.id,
                    gateway_transaction_id=gateway_response.gateway_payment_id,
                    status=gateway_response.status,
                    amount=payment_data.amount,
                    attempt_number=1,
                    request_data=payment_data.dict(),
                    response_data=gateway_response.gateway_response,
                )
                await self.repository.create_transaction(transaction)
            
            await self.repository.update_payment(payment)
            
            return PaymentIntentResponse(
                client_secret=gateway_response.client_secret,
                payment_id=payment.id,
                gateway=gateway_name,
                amount=payment_data.amount,
                currency_code=payment_data.currency_code,
                status=payment.status.value,
                expires_at=payment.expires_at,
            )
            
        except Exception as e:
            logger.error(f"Payment creation failed: {str(e)}")
            raise
    
    async def confirm_payment(
        self,
        payment_id: int,
        payment_method_data: Optional[PaymentMethodCreate] = None
    ) -> PaymentResponse:
        """Confirm and process a payment."""
        try:
            payment = await self.repository.get_payment(payment_id)
            if not payment:
                raise ValueError("Payment not found")
            
            gateway = self._gateways.get(payment.payment_gateway.value)
            if not gateway:
                raise ValueError("Gateway not available")
            
            # Confirm payment with gateway
            gateway_response = await gateway.confirm_payment(
                payment.gateway_payment_id or "",
                payment_method_data,
            )
            
            # Update payment status
            payment.status = gateway_response.status
            payment.processed_at = datetime.utcnow() if gateway_response.success else None
            payment.gateway_response = gateway_response.gateway_response
            
            if not gateway_response.success:
                payment.failure_reason = gateway_response.error_message
            
            # Create transaction record
            transaction = PaymentTransaction(
                payment_id=payment.id,
                gateway_transaction_id=gateway_response.gateway_payment_id,
                status=gateway_response.status,
                amount=payment.amount,
                attempt_number=await self._get_next_attempt_number(payment_id),
                response_data=gateway_response.gateway_response,
                error_message=gateway_response.error_message,
                processed_at=datetime.utcnow(),
            )
            await self.repository.create_transaction(transaction)
            
            await self.repository.update_payment(payment)
            
            return PaymentResponse.from_orm(payment)
            
        except Exception as e:
            logger.error(f"Payment confirmation failed: {str(e)}")
            raise
    
    async def cancel_payment(self, payment_id: int) -> PaymentResponse:
        """Cancel a payment."""
        try:
            payment = await self.repository.get_payment(payment_id)
            if not payment:
                raise ValueError("Payment not found")
            
            if payment.status not in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]:
                raise ValueError("Payment cannot be cancelled")
            
            gateway = self._gateways.get(payment.payment_gateway.value)
            if not gateway:
                raise ValueError("Gateway not available")
            
            # Cancel payment with gateway
            gateway_response = await gateway.cancel_payment(
                payment.gateway_payment_id or ""
            )
            
            # Update payment status
            payment.status = PaymentStatus.CANCELLED
            payment.gateway_response = gateway_response.gateway_response
            
            await self.repository.update_payment(payment)
            
            return PaymentResponse.from_orm(payment)
            
        except Exception as e:
            logger.error(f"Payment cancellation failed: {str(e)}")
            raise
    
    async def refund_payment(
        self,
        payment_id: int,
        refund_data: PaymentRefundCreate
    ) -> PaymentRefundResponse:
        """Process a refund."""
        try:
            payment = await self.repository.get_payment(payment_id)
            if not payment:
                raise ValueError("Payment not found")
            
            if payment.status != PaymentStatus.COMPLETED:
                raise ValueError("Payment must be completed to refund")
            
            if payment.refunded_amount + refund_data.amount > payment.amount:
                raise ValueError("Refund amount exceeds payment amount")
            
            gateway = self._gateways.get(payment.payment_gateway.value)
            if not gateway:
                raise ValueError("Gateway not available")
            
            # Process refund with gateway
            gateway_response = await gateway.refund_payment(
                payment.gateway_payment_id or "",
                refund_data,
            )
            
            # Create refund record
            refund = PaymentRefund(
                payment_id=payment.id,
                gateway_refund_id=gateway_response.gateway_payment_id,
                status=gateway_response.status,
                amount=refund_data.amount,
                reason=refund_data.reason,
                processed_at=datetime.utcnow() if gateway_response.success else None,
                gateway_response=gateway_response.gateway_response,
                failure_reason=gateway_response.error_message,
            )
            
            refund = await self.repository.create_refund(refund)
            
            # Update payment refunded amount
            if gateway_response.success:
                payment.refunded_amount += refund_data.amount
                if payment.refunded_amount >= payment.amount:
                    payment.status = PaymentStatus.REFUNDED
                else:
                    payment.status = PaymentStatus.PARTIALLY_REFUNDED
                
                await self.repository.update_payment(payment)
            
            return PaymentRefundResponse.from_orm(refund)
            
        except Exception as e:
            logger.error(f"Payment refund failed: {str(e)}")
            raise
    
    async def verify_payment(
        self,
        verification_request: PaymentVerificationRequest
    ) -> PaymentVerificationResponse:
        """Verify payment with additional authentication."""
        try:
            payment = await self.repository.get_payment(verification_request.payment_id)
            if not payment:
                raise ValueError("Payment not found")
            
            gateway = self._gateways.get(payment.payment_gateway.value)
            if not gateway:
                raise ValueError("Gateway not available")
            
            # Verify payment with gateway
            verification_response = await gateway.verify_payment(verification_request)
            
            # Update payment status if verification succeeded
            if verification_response.is_verified and verification_response.status == "completed":
                payment.status = PaymentStatus.COMPLETED
                payment.processed_at = datetime.utcnow()
                await self.repository.update_payment(payment)
            
            return verification_response
            
        except Exception as e:
            logger.error(f"Payment verification failed: {str(e)}")
            raise
    
    async def get_payment(self, payment_id: int) -> Optional[PaymentResponse]:
        """Get payment details."""
        payment = await self.repository.get_payment(payment_id)
        return PaymentResponse.from_orm(payment) if payment else None
    
    async def get_payment_transactions(self, payment_id: int) -> List[Any]:
        """Get payment transaction history."""
        return await self.repository.get_payment_transactions(payment_id)
    
    async def get_payment_refunds(self, payment_id: int) -> List[Any]:
        """Get payment refund history."""
        return await self.repository.get_payment_refunds(payment_id)
    
    async def process_webhook(self, webhook_data: PaymentWebhookPayload) -> bool:
        """Process incoming webhook from payment gateway."""
        try:
            gateway = self._gateways.get(webhook_data.gateway)
            if not gateway:
                logger.error(f"Unknown gateway in webhook: {webhook_data.gateway}")
                return False
            
            # Verify webhook signature
            if not await self._verify_webhook_signature(webhook_data):
                logger.error("Webhook signature verification failed")
                return False
            
            # Process webhook based on event type
            await self._process_webhook_event(webhook_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Webhook processing failed: {str(e)}")
            return False
    
    async def _load_gateway_configs(self):
        """Load gateway configurations from database."""
        # This would load from PaymentGatewayConfig table
        # For now, use environment-based config
        pass
    
    async def _initialize_gateways(self):
        """Initialize payment gateway instances."""
        # Initialize Stripe (temporarily disabled)
        # self._gateways["stripe"] = StripeGateway(
        #     config={
        #         "api_key": "sk_test_...",  # Load from secure config
        #         "webhook_secret": "whsec_...",
        #     },
        #     test_mode=True,
        # )
        
        # Initialize PayPal (temporarily disabled)
        # self._gateways["paypal"] = PayPalGateway(
        #     config={
        #         "client_id": "test_client_id",
        #         "client_secret": "test_client_secret",
        #         "webhook_id": "test_webhook_id",
        #     },
        #     test_mode=True,
        # )
        
        # Initialize Adyen
        self._gateways["adyen"] = AdyenGateway(
            config={
                "api_key": "test_api_key",
                "merchant_account": "TestMerchant",
                "client_key": "test_client_key",
            },
            test_mode=True,
        )
    
    async def _validate_order(self, order_id: int, amount: Decimal):
        """Validate order exists and amount matches."""
        # This would check against the Order table
        # For now, assume validation passes
        pass
    
    async def _get_next_attempt_number(self, payment_id: int) -> int:
        """Get next attempt number for transactions."""
        transactions = await self.repository.get_payment_transactions(payment_id)
        return max([t.attempt_number for t in transactions], default=0) + 1
    
    async def _verify_webhook_signature(self, webhook_data: PaymentWebhookPayload) -> bool:
        """Verify webhook signature."""
        # Implement signature verification based on gateway
        return True  # Placeholder
    
    async def _process_webhook_event(self, webhook_data: PaymentWebhookPayload):
        """Process webhook event and update payment status."""
        # Implement webhook processing logic
        pass
