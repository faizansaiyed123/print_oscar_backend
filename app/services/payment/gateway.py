"""Payment gateway abstraction layer."""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.models.payment import PaymentMethod, PaymentStatus
from app.schemas.payment import (
    PaymentCreate,
    PaymentIntentResponse,
    PaymentMethodCreate,
    PaymentRefundCreate,
    PaymentVerificationRequest,
    PaymentVerificationResponse,
)


class GatewayResponse:
    """Standardized response from payment gateways."""
    
    def __init__(
        self,
        success: bool,
        gateway_payment_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        status: PaymentStatus = PaymentStatus.PENDING,
        error_message: Optional[str] = None,
        gateway_response: Optional[Dict[str, Any]] = None,
        fee_amount: Optional[Decimal] = None,
        requires_action: bool = False,
        next_action: Optional[Dict[str, Any]] = None,
    ):
        self.success = success
        self.gateway_payment_id = gateway_payment_id
        self.client_secret = client_secret
        self.status = status
        self.error_message = error_message
        self.gateway_response = gateway_response or {}
        self.fee_amount = fee_amount
        self.requires_action = requires_action
        self.next_action = next_action


class PaymentGateway(ABC):
    """Abstract base class for payment gateways."""
    
    def __init__(self, config: Dict[str, Any], test_mode: bool = True):
        self.config = config
        self.test_mode = test_mode
        self.gateway_name = self.__class__.__name__.lower().replace("gateway", "")
    
    @abstractmethod
    async def create_payment_intent(
        self, 
        payment_data: PaymentCreate,
        order_id: int
    ) -> GatewayResponse:
        """Create a payment intent for the given payment data."""
        pass
    
    @abstractmethod
    async def confirm_payment(
        self,
        gateway_payment_id: str,
        payment_method_data: Optional[PaymentMethodCreate] = None
    ) -> GatewayResponse:
        """Confirm and process a payment."""
        pass
    
    @abstractmethod
    async def cancel_payment(self, gateway_payment_id: str) -> GatewayResponse:
        """Cancel a payment."""
        pass
    
    @abstractmethod
    async def refund_payment(
        self,
        gateway_payment_id: str,
        refund_data: PaymentRefundCreate
    ) -> GatewayResponse:
        """Process a refund."""
        pass
    
    @abstractmethod
    async def retrieve_payment(self, gateway_payment_id: str) -> GatewayResponse:
        """Retrieve payment details from gateway."""
        pass
    
    @abstractmethod
    async def verify_payment(
        self,
        verification_request: PaymentVerificationRequest
    ) -> PaymentVerificationResponse:
        """Verify payment with additional authentication."""
        pass
    
    @abstractmethod
    async def create_payment_method(
        self,
        method_data: PaymentMethodCreate,
        customer_email: str
    ) -> GatewayResponse:
        """Create a payment method for future use."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the gateway is healthy and accessible."""
        pass
    
    @abstractmethod
    def get_supported_payment_methods(self) -> List[PaymentMethod]:
        """Get list of supported payment methods."""
        pass
    
    @abstractmethod
    def get_supported_currencies(self) -> List[str]:
        """Get list of supported currencies."""
        pass
    
    def calculate_fee(self, amount: Decimal) -> Decimal:
        """Calculate gateway fees (override in subclasses)."""
        return Decimal("0.00")
    
    def is_test_mode(self) -> bool:
        """Check if gateway is in test mode."""
        return self.test_mode
    
    def get_gateway_name(self) -> str:
        """Get the gateway name."""
        return self.gateway_name
