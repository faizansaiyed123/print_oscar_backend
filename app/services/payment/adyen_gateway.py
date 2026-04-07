"""Adyen payment gateway implementation."""

import json
import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional

import httpx

from app.models.payment import PaymentMethod, PaymentStatus
from app.schemas.payment import (
    PaymentCreate,
    PaymentMethodCreate,
    PaymentRefundCreate,
    PaymentVerificationRequest,
    PaymentVerificationResponse,
)
from app.services.payment.gateway import GatewayResponse, PaymentGateway


class AdyenGateway(PaymentGateway):
    """Adyen payment gateway implementation."""
    
    def __init__(self, config: Dict[str, Any], test_mode: bool = True):
        super().__init__(config, test_mode)
        
        self.api_key = config.get("api_key")
        self.merchant_account = config.get("merchant_account")
        self.client_key = config.get("client_key")
        self.environment = config.get("environment", "test")  # test or live
        self.hmac_key = config.get("hmac_key")  # For webhook verification
        
        # API endpoints
        if test_mode:
            self.api_url = "https://checkout-test.adyen.com/v68"
        else:
            self.api_url = "https://checkout-live.adyen.com/v68"
        
        self.webhook_username = config.get("webhook_username")
        self.webhook_password = config.get("webhook_password")
    
    async def create_payment_intent(
        self, 
        payment_data: PaymentCreate,
        order_id: int
    ) -> GatewayResponse:
        """Create an Adyen payment session."""
        try:
            # Prepare payment request
            payment_request = {
                "amount": {
                    "currency": payment_data.currency_code,
                    "value": int(payment_data.amount * 100),  # Convert to cents
                },
                "reference": f"order_{order_id}",
                "merchantAccount": self.merchant_account,
                "returnUrl": f"https://yourstore.com/payment/return?order_id={order_id}",
                "countryCode": "US",  # Should be derived from customer location
                "shopperEmail": payment_data.customer_email,
                "shopperReference": payment_data.customer_email,
                "channel": "web",
                "additionalData": {
                    "allow3DS2": "true",
                    "executeThreeD": "true",
                },
                "metadata": {
                    "order_id": str(order_id),
                    "payment_id": str(payment_data.payment_metadata.get("payment_id", "")),
                },
            }
            
            # Add payment method if provided
            if payment_data.payment_method.card_token:
                payment_request["paymentMethod"] = {
                    "type": "scheme",
                    "storedPaymentMethodId": payment_data.payment_method.card_token,
                }
            
            # Make API request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/payments",
                    headers={
                        "X-API-Key": self.api_key,
                        "Content-Type": "application/json",
                    },
                    json=payment_request,
                )
                response.raise_for_status()
                result = response.json()
            
            # Calculate Adyen fees (varies by payment method and region)
            fee_amount = self.calculate_fee(payment_data.amount)
            
            # Determine if additional action is required
            requires_action = result.get("action") is not None
            
            return GatewayResponse(
                success=True,
                gateway_payment_id=result.get("pspReference"),
                client_secret=result.get("details", {}).get("paymentData"),
                status=self._map_adyen_status(result.get("resultCode", "Pending")),
                gateway_response=result,
                fee_amount=fee_amount,
                requires_action=requires_action,
                next_action=result.get("action") if requires_action else None,
            )
            
        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response.content else {}
            return GatewayResponse(
                success=False,
                error_message=f"Adyen API error: {error_data.get('message', str(e))}",
                status=PaymentStatus.FAILED,
                gateway_response={"error": error_data},
            )
        except Exception as e:
            return GatewayResponse(
                success=False,
                error_message=f"Adyen error: {str(e)}",
                status=PaymentStatus.FAILED,
                gateway_response={"error": str(e)},
            )
    
    async def confirm_payment(
        self,
        gateway_payment_id: str,
        payment_method_data: Optional[PaymentMethodCreate] = None
    ) -> GatewayResponse:
        """Confirm payment with additional details."""
        try:
            # Adyen uses payment details submission for confirmation
            # This would typically be called after 3D Secure verification
            payment_request = {
                "paymentData": payment_method_data.card_token if payment_method_data else "",
                "merchantAccount": self.merchant_account,
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/payments/details",
                    headers={
                        "X-API-Key": self.api_key,
                        "Content-Type": "application/json",
                    },
                    json=payment_request,
                )
                response.raise_for_status()
                result = response.json()
            
            return GatewayResponse(
                success=True,
                gateway_payment_id=result.get("pspReference"),
                status=self._map_adyen_status(result.get("resultCode", "Pending")),
                gateway_response=result,
            )
            
        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response.content else {}
            return GatewayResponse(
                success=False,
                error_message=f"Adyen confirmation error: {error_data.get('message', str(e))}",
                status=PaymentStatus.FAILED,
                gateway_response={"error": error_data},
            )
        except Exception as e:
            return GatewayResponse(
                success=False,
                error_message=f"Adyen confirmation error: {str(e)}",
                status=PaymentStatus.FAILED,
                gateway_response={"error": str(e)},
            )
    
    async def cancel_payment(self, gateway_payment_id: str) -> GatewayResponse:
        """Cancel an Adyen payment."""
        try:
            cancel_request = {
                "merchantAccount": self.merchant_account,
                "originalReference": gateway_payment_id,
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/cancels",
                    headers={
                        "X-API-Key": self.api_key,
                        "Content-Type": "application/json",
                    },
                    json=cancel_request,
                )
                response.raise_for_status()
                result = response.json()
            
            return GatewayResponse(
                success=True,
                gateway_payment_id=result.get("pspReference"),
                status=self._map_adyen_status(result.get("resultCode", "Pending")),
                gateway_response=result,
            )
            
        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response.content else {}
            return GatewayResponse(
                success=False,
                error_message=f"Adyen cancel error: {error_data.get('message', str(e))}",
                status=PaymentStatus.FAILED,
                gateway_response={"error": error_data},
            )
        except Exception as e:
            return GatewayResponse(
                success=False,
                error_message=f"Adyen cancel error: {str(e)}",
                status=PaymentStatus.FAILED,
                gateway_response={"error": str(e)},
            )
    
    async def refund_payment(
        self,
        gateway_payment_id: str,
        refund_data: PaymentRefundCreate
    ) -> GatewayResponse:
        """Process an Adyen refund."""
        try:
            refund_request = {
                "merchantAccount": self.merchant_account,
                "originalReference": gateway_payment_id,
                "amount": {
                    "currency": "USD",  # Should match original currency
                    "value": int(refund_data.amount * 100),
                },
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/refunds",
                    headers={
                        "X-API-Key": self.api_key,
                        "Content-Type": "application/json",
                    },
                    json=refund_request,
                )
                response.raise_for_status()
                result = response.json()
            
            return GatewayResponse(
                success=True,
                gateway_payment_id=result.get("pspReference"),
                status=self._map_adyen_status(result.get("resultCode", "Pending")),
                gateway_response=result,
            )
            
        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response.content else {}
            return GatewayResponse(
                success=False,
                error_message=f"Adyen refund error: {error_data.get('message', str(e))}",
                status=PaymentStatus.FAILED,
                gateway_response={"error": error_data},
            )
        except Exception as e:
            return GatewayResponse(
                success=False,
                error_message=f"Adyen refund error: {str(e)}",
                status=PaymentStatus.FAILED,
                gateway_response={"error": str(e)},
            )
    
    async def retrieve_payment(self, gateway_payment_id: str) -> GatewayResponse:
        """Retrieve payment details from Adyen."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/payments/{gateway_payment_id}",
                    headers={
                        "X-API-Key": self.api_key,
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()
                result = response.json()
            
            return GatewayResponse(
                success=True,
                gateway_payment_id=result.get("pspReference"),
                status=self._map_adyen_status(result.get("resultCode", "Pending")),
                gateway_response=result,
            )
            
        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response.content else {}
            return GatewayResponse(
                success=False,
                error_message=f"Adyen retrieve error: {error_data.get('message', str(e))}",
                status=PaymentStatus.FAILED,
                gateway_response={"error": error_data},
            )
        except Exception as e:
            return GatewayResponse(
                success=False,
                error_message=f"Adyen retrieve error: {str(e)}",
                status=PaymentStatus.FAILED,
                gateway_response={"error": str(e)},
            )
    
    async def verify_payment(
        self,
        verification_request: PaymentVerificationRequest
    ) -> PaymentVerificationResponse:
        """Verify payment after additional authentication."""
        try:
            # Submit payment details for verification
            details = verification_request.verification_data.get("details", {})
            
            payment_request = {
                "paymentData": verification_request.verification_data.get("payment_data"),
                "details": details,
                "merchantAccount": self.merchant_account,
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/payments/details",
                    headers={
                        "X-API-Key": self.api_key,
                        "Content-Type": "application/json",
                    },
                    json=payment_request,
                )
                response.raise_for_status()
                result = response.json()
            
            result_code = result.get("resultCode", "Pending")
            
            if result_code == "Authorised":
                return PaymentVerificationResponse(
                    payment_id=verification_request.payment_id,
                    status="completed",
                    is_verified=True,
                    verification_method=verification_request.verification_method,
                )
            elif result_code in ["Pending", "Received"]:
                return PaymentVerificationResponse(
                    payment_id=verification_request.payment_id,
                    status="pending",
                    is_verified=False,
                    verification_method=verification_request.verification_method,
                )
            else:
                return PaymentVerificationResponse(
                    payment_id=verification_request.payment_id,
                    status="failed",
                    is_verified=False,
                    verification_method=verification_request.verification_method,
                    error_message=f"Adyen result: {result_code}",
                )
                
        except Exception as e:
            return PaymentVerificationResponse(
                payment_id=verification_request.payment_id,
                status="failed",
                is_verified=False,
                verification_method=verification_request.verification_method,
                error_message=f"Adyen verification error: {str(e)}",
            )
    
    async def create_payment_method(
        self,
        method_data: PaymentMethodCreate,
        customer_email: str
    ) -> GatewayResponse:
        """Create a recurring payment method."""
        try:
            # Create recurring payment method
            payment_request = {
                "amount": {"currency": "USD", "value": 0},  # Zero amount for tokenization
                "paymentMethod": {
                    "type": "scheme",
                    "number": method_data.card_last4,
                    "expiryMonth": str(method_data.card_exp_month).zfill(2),
                    "expiryYear": str(method_data.card_exp_year),
                },
                "reference": f"token_{uuid.uuid4().hex[:8]}",
                "merchantAccount": self.merchant_account,
                "shopperEmail": customer_email,
                "shopperReference": customer_email,
                "recurring": {
                    "contract": "RECURRING",
                },
                "storePaymentMethod": True,
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/payments",
                    headers={
                        "X-API-Key": self.api_key,
                        "Content-Type": "application/json",
                    },
                    json=payment_request,
                )
                response.raise_for_status()
                result = response.json()
            
            return GatewayResponse(
                success=True,
                gateway_payment_id=result.get("recurringDetailReference"),
                status=PaymentStatus.COMPLETED,
                gateway_response=result,
            )
            
        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response.content else {}
            return GatewayResponse(
                success=False,
                error_message=f"Adyen tokenization error: {error_data.get('message', str(e))}",
                status=PaymentStatus.FAILED,
                gateway_response={"error": error_data},
            )
        except Exception as e:
            return GatewayResponse(
                success=False,
                error_message=f"Adyen tokenization error: {str(e)}",
                status=PaymentStatus.FAILED,
                gateway_response={"error": str(e)},
            )
    
    async def health_check(self) -> bool:
        """Check if Adyen is accessible."""
        try:
            # Make a simple API call to check connectivity
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/paymentMethods",
                    headers={
                        "X-API-Key": self.api_key,
                        "Content-Type": "application/json",
                    },
                    params={"merchantAccount": self.merchant_account},
                    timeout=10.0,
                )
                return response.status_code == 200
        except Exception:
            return False
    
    def get_supported_payment_methods(self) -> List[PaymentMethod]:
        """Get supported payment methods for Adyen."""
        return [
            PaymentMethod.CARD,
            PaymentMethod.DIGITAL_WALLET,  # Apple Pay, Google Pay, PayPal
            PaymentMethod.BANK_TRANSFER,  # SEPA, ACH
            PaymentMethod.BUY_NOW_PAY_LATER,  # Klarna, Afterpay
        ]
    
    def get_supported_currencies(self) -> List[str]:
        """Get supported currencies for Adyen."""
        return [
            "USD", "EUR", "GBP", "CAD", "AUD", "CHF", "SEK", "NOK", "DKK",
            "PLN", "CZK", "HUF", "RON", "BGN", "HRK", "RUB", "UAH",
            "MXN", "BRL", "ARS", "CLP", "COP", "PEN", "UYU",
            "JPY", "SGD", "HKD", "CNY", "INR", "THB", "MYR", "IDR",
            "PHP", "VND", "KRW", "TWD", "NZD", "AED", "SAR", "ZAR"
        ]
    
    def calculate_fee(self, amount: Decimal) -> Decimal:
        """Calculate Adyen fees (varies by method, using European card average)."""
        percentage_fee = amount * Decimal("0.028")  # 2.8%
        fixed_fee = Decimal("0.25")  # €0.25, converted to USD equivalent
        return percentage_fee + fixed_fee
    
    def _map_adyen_status(self, adyen_result: str) -> PaymentStatus:
        """Map Adyen result codes to our PaymentStatus enum."""
        status_mapping = {
            "Authorised": PaymentStatus.COMPLETED,
            "Pending": PaymentStatus.PENDING,
            "Received": PaymentStatus.PENDING,
            "IdentifyShopper": PaymentStatus.PENDING,
            "ChallengeShopper": PaymentStatus.PENDING,
            "RedirectShopper": PaymentStatus.PENDING,
            "Refused": PaymentStatus.FAILED,
            "Cancelled": PaymentStatus.CANCELLED,
            "Error": PaymentStatus.FAILED,
        }
        return status_mapping.get(adyen_result, PaymentStatus.FAILED)
