"""Payment retry mechanism and failure handling."""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from app.models.payment import Payment, PaymentStatus, PaymentTransaction
from app.services.payment.gateway import GatewayResponse, PaymentGateway

logger = logging.getLogger(__name__)


class RetryStrategy(str, Enum):
    """Retry strategies for failed payments."""
    IMMEDIATE = "immediate"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_INTERVAL = "fixed_interval"


class FailureType(str, Enum):
    """Types of payment failures."""
    TEMPORARY = "temporary"  # Network issues, gateway downtime
    PERMANENT = "permanent"  # Invalid card, insufficient funds
    RATE_LIMIT = "rate_limit"  # Gateway rate limiting
    VERIFICATION = "verification"  # 3D Secure, additional auth required


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_retries: int = 3,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
        base_delay: timedelta = timedelta(seconds=1),
        max_delay: timedelta = timedelta(minutes=5),
        retry_on_status_codes: List[int] = None,
        retry_on_failure_types: List[FailureType] = None,
    ):
        self.max_retries = max_retries
        self.strategy = strategy
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.retry_on_status_codes = retry_on_status_codes or [500, 502, 503, 504, 429]
        self.retry_on_failure_types = retry_on_failure_types or [
            FailureType.TEMPORARY,
            FailureType.RATE_LIMIT,
        ]


class PaymentRetryManager:
    """Manages payment retries with intelligent backoff."""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self._retry_queue = asyncio.Queue()
        self._active_retries = {}
        self._retry_stats = {
            "total_retries": 0,
            "successful_retries": 0,
            "failed_retries": 0,
        }
    
    async def schedule_retry(
        self,
        payment: Payment,
        gateway: PaymentGateway,
        operation: str,
        attempt_number: int,
        failure_type: FailureType,
        error_message: str,
    ) -> bool:
        """Schedule a payment retry."""
        try:
            # Check if retry should be attempted
            if not self._should_retry(payment, attempt_number, failure_type):
                logger.info(f"Payment {payment.id} not eligible for retry")
                return False
            
            # Calculate retry delay
            delay = self._calculate_retry_delay(attempt_number, failure_type)
            
            # Schedule retry
            retry_task = {
                "payment": payment,
                "gateway": gateway,
                "operation": operation,
                "attempt_number": attempt_number + 1,
                "scheduled_at": datetime.utcnow() + delay,
                "failure_type": failure_type,
                "error_message": error_message,
            }
            
            await self._retry_queue.put(retry_task)
            self._active_retries[payment.id] = retry_task
            
            logger.info(f"Scheduled retry for payment {payment.id} in {delay.total_seconds()} seconds")
            return True
            
        except Exception as e:
            logger.error(f"Failed to schedule retry for payment {payment.id}: {str(e)}")
            return False
    
    async def process_retries(self):
        """Process scheduled retries."""
        while True:
            try:
                # Get next retry task
                retry_task = await self._retry_queue.get()
                
                # Check if it's time to retry
                if datetime.utcnow() < retry_task["scheduled_at"]:
                    # Put it back and wait
                    await asyncio.sleep(1)
                    await self._retry_queue.put(retry_task)
                    continue
                
                # Execute retry
                await self._execute_retry(retry_task)
                
            except Exception as e:
                logger.error(f"Error processing retry queue: {str(e)}")
                await asyncio.sleep(5)
    
    async def _execute_retry(self, retry_task: Dict[str, Any]):
        """Execute a retry attempt."""
        payment = retry_task["payment"]
        gateway = retry_task["gateway"]
        operation = retry_task["operation"]
        attempt_number = retry_task["attempt_number"]
        
        try:
            logger.info(f"Executing retry {attempt_number} for payment {payment.id}")
            
            # Execute the appropriate operation
            if operation == "create_payment_intent":
                response = await self._retry_create_payment(payment, gateway)
            elif operation == "confirm_payment":
                response = await self._retry_confirm_payment(payment, gateway)
            elif operation == "refund_payment":
                response = await self._retry_refund_payment(payment, gateway)
            else:
                logger.error(f"Unknown retry operation: {operation}")
                return
            
            # Update retry statistics
            self._retry_stats["total_retries"] += 1
            
            if response.success:
                self._retry_stats["successful_retries"] += 1
                logger.info(f"Retry successful for payment {payment.id}")
                
                # Remove from active retries
                self._active_retries.pop(payment.id, None)
            else:
                self._retry_stats["failed_retries"] += 1
                
                # Determine if we should retry again
                failure_type = self._classify_failure(response.error_message)
                
                if attempt_number < self.config.max_retries:
                    await self.schedule_retry(
                        payment, gateway, operation, attempt_number, failure_type, response.error_message
                    )
                else:
                    logger.error(f"Max retries exceeded for payment {payment.id}")
                    self._active_retries.pop(payment.id, None)
            
        except Exception as e:
            logger.error(f"Retry execution failed for payment {payment.id}: {str(e)}")
            self._active_retries.pop(payment.id, None)
    
    async def _retry_create_payment(self, payment: Payment, gateway: PaymentGateway) -> GatewayResponse:
        """Retry payment creation."""
        # This would reconstruct the payment data and retry
        # For now, return a failure response
        return GatewayResponse(
            success=False,
            error_message="Retry not implemented for create_payment",
            status=PaymentStatus.FAILED,
        )
    
    async def _retry_confirm_payment(self, payment: Payment, gateway: PaymentGateway) -> GatewayResponse:
        """Retry payment confirmation."""
        if not payment.gateway_payment_id:
            return GatewayResponse(
                success=False,
                error_message="No gateway payment ID available",
                status=PaymentStatus.FAILED,
            )
        
        return await gateway.confirm_payment(payment.gateway_payment_id)
    
    async def _retry_refund_payment(self, payment: Payment, gateway: PaymentGateway) -> GatewayResponse:
        """Retry refund processing."""
        # This would get the refund data and retry
        return GatewayResponse(
            success=False,
            error_message="Retry not implemented for refund_payment",
            status=PaymentStatus.FAILED,
        )
    
    def _should_retry(self, payment: Payment, attempt_number: int, failure_type: FailureType) -> bool:
        """Determine if a payment should be retried."""
        # Check max attempts
        if attempt_number >= self.config.max_retries:
            return False
        
        # Check failure type
        if failure_type not in self.config.retry_on_failure_types:
            return False
        
        # Check payment status
        if payment.status in [PaymentStatus.COMPLETED, PaymentStatus.CANCELLED, PaymentStatus.REFUNDED]:
            return False
        
        return True
    
    def _calculate_retry_delay(self, attempt_number: int, failure_type: FailureType) -> timedelta:
        """Calculate delay before next retry."""
        if failure_type == FailureType.RATE_LIMIT:
            # Longer delay for rate limiting
            return min(
                timedelta(seconds=60 * attempt_number),
                self.config.max_delay
            )
        
        if self.config.strategy == RetryStrategy.IMMEDIATE:
            return timedelta(seconds=0)
        elif self.config.strategy == RetryStrategy.FIXED_INTERVAL:
            return self.config.base_delay
        elif self.config.strategy == RetryStrategy.LINEAR_BACKOFF:
            return min(
                self.config.base_delay * attempt_number,
                self.config.max_delay
            )
        elif self.config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.config.base_delay * (2 ** (attempt_number - 1))
            return min(delay, self.config.max_delay)
        
        return self.config.base_delay
    
    def _classify_failure(self, error_message: str) -> FailureType:
        """Classify the type of failure based on error message."""
        error_lower = error_message.lower()
        
        if any(keyword in error_lower for keyword in ["timeout", "network", "connection"]):
            return FailureType.TEMPORARY
        elif any(keyword in error_lower for keyword in ["rate limit", "too many requests"]):
            return FailureType.RATE_LIMIT
        elif any(keyword in error_lower for keyword in ["3d", "verification", "authenticate"]):
            return FailureType.VERIFICATION
        elif any(keyword in error_lower for keyword in ["insufficient", "declined", "invalid"]):
            return FailureType.PERMANENT
        else:
            return FailureType.TEMPORARY
    
    def get_retry_stats(self) -> Dict[str, Any]:
        """Get retry statistics."""
        return {
            **self._retry_stats,
            "active_retries": len(self._active_retries),
            "queue_size": self._retry_queue.qsize(),
        }
    
    def cancel_retry(self, payment_id: int) -> bool:
        """Cancel scheduled retry for a payment."""
        if payment_id in self._active_retries:
            del self._active_retries[payment_id]
            logger.info(f"Cancelled retry for payment {payment_id}")
            return True
        return False


class CircuitBreaker:
    """Circuit breaker pattern for gateway failures."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: timedelta = timedelta(minutes=1),
        expected_exception: type = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt to reset."""
        return (
            self.last_failure_time and
            datetime.utcnow() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


class PaymentFailureHandler:
    """Handles payment failures and recovery."""
    
    def __init__(self, retry_manager: PaymentRetryManager):
        self.retry_manager = retry_manager
        self.circuit_breakers = {}
    
    async def handle_payment_failure(
        self,
        payment: Payment,
        gateway: PaymentGateway,
        operation: str,
        error_message: str,
        gateway_response: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Handle a payment failure."""
        try:
            # Classify the failure
            failure_type = self._classify_failure(error_message, gateway_response)
            
            # Log the failure
            await self._log_failure(payment, gateway, operation, failure_type, error_message)
            
            # Update payment status
            if failure_type == FailureType.PERMANENT:
                payment.status = PaymentStatus.FAILED
                payment.failure_reason = error_message
                # Don't retry permanent failures
                return False
            elif failure_type == FailureType.VERIFICATION:
                # Set to pending verification
                payment.status = PaymentStatus.PENDING
                # Don't retry verification failures automatically
                return False
            else:
                # Schedule retry for temporary failures
                attempt_number = await self._get_attempt_number(payment)
                return await self.retry_manager.schedule_retry(
                    payment, gateway, operation, attempt_number, failure_type, error_message
                )
                
        except Exception as e:
            logger.error(f"Error handling payment failure: {str(e)}")
            return False
    
    def _classify_failure(
        self, 
        error_message: str, 
        gateway_response: Optional[Dict[str, Any]]
    ) -> FailureType:
        """Classify the type of failure."""
        error_lower = error_message.lower()
        
        # Check gateway response for specific error codes
        if gateway_response:
            error_code = gateway_response.get("error", {}).get("code", "").lower()
            
            if error_code in ["rate_limit", "too_many_requests"]:
                return FailureType.RATE_LIMIT
            elif error_code in ["insufficient_funds", "card_declined", "do_not_honor"]:
                return FailureType.PERMANENT
            elif error_code in ["3d_secure_required", "verification_required"]:
                return FailureType.VERIFICATION
        
        # Classify based on error message
        if any(keyword in error_lower for keyword in ["timeout", "network", "connection"]):
            return FailureType.TEMPORARY
        elif any(keyword in error_lower for keyword in ["rate limit", "too many requests"]):
            return FailureType.RATE_LIMIT
        elif any(keyword in error_lower for keyword in ["3d", "verification", "authenticate"]):
            return FailureType.VERIFICATION
        elif any(keyword in error_lower for keyword in ["insufficient", "declined", "invalid"]):
            return FailureType.PERMANENT
        else:
            return FailureType.TEMPORARY
    
    async def _log_failure(
        self,
        payment: Payment,
        gateway: PaymentGateway,
        operation: str,
        failure_type: FailureType,
        error_message: str,
    ):
        """Log payment failure for analysis."""
        # This would log to your monitoring system
        logger.error(
            f"Payment failure - ID: {payment.id}, "
            f"Gateway: {gateway.get_gateway_name()}, "
            f"Operation: {operation}, "
            f"Type: {failure_type.value}, "
            f"Error: {error_message}"
        )
    
    async def _get_attempt_number(self, payment: Payment) -> int:
        """Get current attempt number for payment."""
        # This would query the transaction repository
        return 1
    
    def get_circuit_breaker(self, gateway_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for gateway."""
        if gateway_name not in self.circuit_breakers:
            self.circuit_breakers[gateway_name] = CircuitBreaker()
        return self.circuit_breakers[gateway_name]
