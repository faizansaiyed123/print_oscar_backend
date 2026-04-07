"""PayPal payment gateway implementation."""

import json
from decimal import Decimal
from typing import Any, Dict, List, Optional

import httpx
import paypalrestsdk as paypal

from app.models.payment import PaymentMethod, PaymentStatus
from app.schemas.payment import (
    PaymentCreate,
    PaymentMethodCreate,
    PaymentRefundCreate,
    PaymentVerificationRequest,
    PaymentVerificationResponse,
)
from app.services.payment.gateway import GatewayResponse, PaymentGateway


class PayPalGateway(PaymentGateway):
    """PayPal payment gateway implementation."""
    
    def __init__(self, config: Dict[str, Any], test_mode: bool = True):
        super().__init__(config, test_mode)
        
        # Configure PayPal SDK
        if test_mode:
            paypal.configure({
                'mode': 'sandbox',  # sandbox or live
                'client_id': config.get("client_id") or "test_client_id",
                'client_secret': config.get("client_secret") or "test_client_secret",
            })
        else:
            paypal.configure({
                'mode': 'live',
                'client_id': config.get("client_id"),
                'client_secret': config.get("client_secret"),
            })
        
        self.return_url = config.get("return_url", "https://yourstore.com/payment/return")
        self.cancel_url = config.get("cancel_url", "https://yourstore.com/payment/cancel")
    
    async def create_payment_intent(
        self, 
        payment_data: PaymentCreate,
        order_id: int
    ) -> GatewayResponse:
        """Create a PayPal payment."""
        try:
            # Create PayPal payment using the REST SDK
            payment = paypal.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "redirect_urls": {
                    "return_url": self.return_url,
                    "cancel_url": self.cancel_url
                },
                "transactions": [{
                    "item_list": {
                        "items": [{
                            "name": f"Order #{order_id}",
                            "sku": str(order_id),
                            "price": str(payment_data.amount),
                            "currency": payment_data.currency_code,
                            "quantity": 1
                        }]
                    },
                    "amount": {
                        "total": str(payment_data.amount),
                        "currency": payment_data.currency_code
                    },
                    "description": f"Order #{order_id}"
                }]
            })
            
            # Create payment
            if payment.create():
                # Calculate PayPal fees
                fee_amount = self.calculate_fee(payment_data.amount)
                
                # Extract approval URL for redirect
                approval_url = None
                for link in payment.links:
                    if link.rel == "approval_url":
                        approval_url = link.href
                        break
                
                return GatewayResponse(
                    success=True,
                    gateway_payment_id=payment.id,
                    status=PaymentStatus.PENDING,
                    gateway_response={"id": payment.id, "links": [link.href for link in payment.links]},
                    fee_amount=fee_amount,
                    requires_action=True,
                    next_action={
                        "type": "redirect",
                        "url": approval_url,
                        "payment_id": payment.id,
                    } if approval_url else None,
                )
            else:
                return GatewayResponse(
                    success=False,
                    error_message=f"PayPal error: {payment.error}",
                    status=PaymentStatus.FAILED,
                    gateway_response={"error": payment.error}
                )
                
        except Exception as e:
            return GatewayResponse(
                success=False,
                error_message=f"PayPal error: {str(e)}",
                status=PaymentStatus.FAILED,
                gateway_response={"error": str(e)}
            )
    
    async def confirm_payment(
        self,
        gateway_payment_id: str,
        payment_method_data: Optional[PaymentMethodCreate] = None
    ) -> GatewayResponse:
        """Execute a PayPal payment."""
        try:
            # Find and execute the payment
            payment = paypal.Payment.find(gateway_payment_id)
            
            if payment.execute({"payer_id": payment_method_data.payment_method_data.get("payer_id", "")}):
                return GatewayResponse(
                    success=True,
                    gateway_payment_id=payment.id,
                    status=PaymentStatus.COMPLETED,
                    gateway_response=dict(payment),
                )
            else:
                return GatewayResponse(
                    success=False,
                    error_message=f"PayPal execution failed: {payment.error}",
                    status=PaymentStatus.FAILED,
                    gateway_response={"error": payment.error}
                )
            
        except Exception as e:
            return GatewayResponse(
                success=False,
                error_message=f"PayPal confirm error: {str(e)}",
                status=PaymentStatus.FAILED,
                gateway_response={"error": str(e)}
            )
    
    async def cancel_payment(self, gateway_payment_id: str) -> GatewayResponse:
        """Cancel a PayPal payment."""
        try:
            # PayPal payments expire if not approved
            return GatewayResponse(
                success=True,
                gateway_payment_id=gateway_payment_id,
                status=PaymentStatus.CANCELLED,
                gateway_response={"cancelled": True},
            )
            
        except Exception as e:
            return GatewayResponse(
                success=False,
                error_message=f"PayPal cancel error: {str(e)}",
                status=PaymentStatus.FAILED,
                gateway_response={"error": str(e)}
            )
    
    async def refund_payment(
        self,
        gateway_payment_id: str,
        refund_data: PaymentRefundCreate
    ) -> GatewayResponse:
        """Process a PayPal refund."""
        try:
            # Find the payment
            payment = paypal.Payment.find(gateway_payment_id)
            
            # Get the sale ID from the transaction
            sale_id = None
            for transaction in payment.transactions:
                if transaction.related_resources:
                    for related in transaction.related_resources:
                        if hasattr(related, 'sale'):
                            sale_id = related.sale.id
                            break
            
            if not sale_id:
                return GatewayResponse(
                    success=False,
                    error_message="No sale found for refund",
                    status=PaymentStatus.FAILED,
                )
            
            # Create refund
            sale = paypal.Sale.find(sale_id)
            refund = sale.refund({
                "amount": {
                    "total": str(refund_data.amount),
                    "currency": "USD"
                }
            })
            
            return GatewayResponse(
                success=True,
                gateway_payment_id=refund.id,
                status=self._map_refund_status(refund.state),
                gateway_response=dict(refund),
            )
            
        except Exception as e:
            return GatewayResponse(
                success=False,
                error_message=f"PayPal refund error: {str(e)}",
                status=PaymentStatus.FAILED,
                gateway_response={"error": str(e)}
            )
    
    async def retrieve_payment(self, gateway_payment_id: str) -> GatewayResponse:
        """Retrieve payment details from PayPal."""
        try:
            payment = paypal.Payment.find(gateway_payment_id)
            
            return GatewayResponse(
                success=True,
                gateway_payment_id=payment.id,
                status=self._map_paypal_status(payment.state),
                gateway_response=dict(payment),
            )
            
        except Exception as e:
            return GatewayResponse(
                success=False,
                error_message=f"PayPal retrieve error: {str(e)}",
                status=PaymentStatus.FAILED,
                gateway_response={"error": str(e)}
            )
    
    async def verify_payment(
        self,
        verification_request: PaymentVerificationRequest
    ) -> PaymentVerificationResponse:
        """Verify PayPal payment after return."""
        try:
            # Get the payment details
            payment = paypal.Payment.find(
                verification_request.verification_data.get("payment_id")
            )
            
            if payment.state == "approved":
                return PaymentVerificationResponse(
                    payment_id=verification_request.payment_id,
                    status="completed",
                    is_verified=True,
                    verification_method=verification_request.verification_method,
                )
            else:
                return PaymentVerificationResponse(
                    payment_id=verification_request.payment_id,
                    status="failed",
                    is_verified=False,
                    verification_method=verification_request.verification_method,
                    error_message=f"PayPal payment state: {payment.state}",
                )
                
        except Exception as e:
            return PaymentVerificationResponse(
                payment_id=verification_request.payment_id,
                status="failed",
                is_verified=False,
                verification_method=verification_request.verification_method,
                error_message=f"PayPal verification error: {str(e)}",
            )
    
    async def create_payment_method(
        self,
        method_data: PaymentMethodCreate,
        customer_email: str
    ) -> GatewayResponse:
        """PayPal doesn't support stored payment methods in the same way."""
        return GatewayResponse(
            success=False,
            error_message="PayPal vaulted payments require additional setup",
            status=PaymentStatus.FAILED,
        )
    
    async def health_check(self) -> bool:
        """Check if PayPal is accessible."""
        try:
            # Try to find a dummy payment to test connectivity
            paypal.Payment.find("test")
            return True
        except Exception:
            return False
    
    def get_supported_payment_methods(self) -> List[PaymentMethod]:
        """Get supported payment methods for PayPal."""
        return [
            PaymentMethod.DIGITAL_WALLET,  # PayPal account
            PaymentMethod.BANK_TRANSFER,  # PayPal bank transfer
            PaymentMethod.BUY_NOW_PAY_LATER,  # PayPal Credit, Pay in 4
        ]
    
    def get_supported_currencies(self) -> List[str]:
        """Get supported currencies for PayPal."""
        return [
            "USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CNY", "INR",
            "BRL", "MXN", "CHF", "SEK", "NOK", "DKK", "PLN", "CZK",
            "HUF", "ILS", "NZD", "SGD", "HKD", "TWD", "THB", "PHP"
        ]
    
    def calculate_fee(self, amount: Decimal) -> Decimal:
        """Calculate PayPal fees (2.9% + $0.30 for domestic)."""
        percentage_fee = amount * Decimal("0.029")  # 2.9%
        fixed_fee = Decimal("0.30")
        return percentage_fee + fixed_fee
    
    def _map_paypal_status(self, paypal_status: str) -> PaymentStatus:
        """Map PayPal status to our PaymentStatus enum."""
        status_mapping = {
            "created": PaymentStatus.PENDING,
            "approved": PaymentStatus.COMPLETED,
            "failed": PaymentStatus.FAILED,
            "canceled": PaymentStatus.CANCELLED,
        }
        return status_mapping.get(paypal_status, PaymentStatus.FAILED)
    
    def _map_refund_status(self, refund_status: str) -> PaymentStatus:
        """Map PayPal refund status to our PaymentStatus enum."""
        status_mapping = {
            "pending": PaymentStatus.PENDING,
            "completed": PaymentStatus.COMPLETED,
            "failed": PaymentStatus.FAILED,
            "cancelled": PaymentStatus.CANCELLED,
        }
        return status_mapping.get(refund_status, PaymentStatus.FAILED)
