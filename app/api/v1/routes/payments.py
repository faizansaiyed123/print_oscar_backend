"""Payment API endpoints."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.payment import (
    PaymentCreate,
    PaymentIntentResponse,
    PaymentMethodCreate,
    PaymentRefundCreate,
    PaymentRefundResponse,
    PaymentResponse,
    PaymentTransactionResponse,
    PaymentVerificationRequest,
    PaymentVerificationResponse,
    PaymentWebhookPayload,
)
from app.services.payment.service import PaymentService

router = APIRouter()


@router.post("/payments", response_model=PaymentIntentResponse)
async def create_payment(
    payment_data: PaymentCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Create a new payment."""
    try:
        payment_service = PaymentService(db)
        await payment_service.initialize()
        
        # Get client IP for fraud detection
        client_ip = request.client.host
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        # Create payment
        payment_intent = await payment_service.create_payment(
            payment_data=payment_data,
            customer_ip=client_ip,
        )
        
        return payment_intent
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment creation failed: {str(e)}"
        )


@router.post("/payments/{payment_id}/confirm", response_model=PaymentResponse)
async def confirm_payment(
    payment_id: int,
    payment_method_data: Optional[PaymentMethodCreate] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Confirm and process a payment."""
    try:
        payment_service = PaymentService(db)
        await payment_service.initialize()
        
        payment = await payment_service.confirm_payment(
            payment_id=payment_id,
            payment_method_data=payment_method_data,
        )
        
        return payment
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment confirmation failed: {str(e)}"
        )


@router.post("/payments/{payment_id}/cancel", response_model=PaymentResponse)
async def cancel_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Cancel a payment."""
    try:
        payment_service = PaymentService(db)
        await payment_service.initialize()
        
        payment = await payment_service.cancel_payment(payment_id=payment_id)
        
        return payment
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment cancellation failed: {str(e)}"
        )


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Get payment details."""
    try:
        payment_service = PaymentService(db)
        await payment_service.initialize()
        
        payment = await payment_service.get_payment(payment_id=payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        # Check if user has permission to view this payment
        if current_user and current_user.email != payment.customer_email:
            # In production, check if user is admin or has permission
            pass
        
        return payment
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve payment: {str(e)}"
        )


@router.get("/payments/{payment_id}/transactions", response_model=List[PaymentTransactionResponse])
async def get_payment_transactions(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Get payment transaction history."""
    try:
        payment_service = PaymentService(db)
        await payment_service.initialize()
        
        # First check if payment exists and user has permission
        payment = await payment_service.get_payment(payment_id=payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        if current_user and current_user.email != payment.customer_email:
            # Check permissions
            pass
        
        transactions = await payment_service.get_payment_transactions(payment_id=payment_id)
        return [PaymentTransactionResponse.from_orm(t) for t in transactions]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve transactions: {str(e)}"
        )


@router.post("/payments/{payment_id}/refunds", response_model=PaymentRefundResponse)
async def refund_payment(
    payment_id: int,
    refund_data: PaymentRefundCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Process a refund."""
    try:
        payment_service = PaymentService(db)
        await payment_service.initialize()
        
        # Check permissions (only admin or order owner can refund)
        payment = await payment_service.get_payment(payment_id=payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        # In production, implement proper permission checking
        if current_user and not current_user.is_admin:
            # Check if user owns the order
            pass
        
        refund = await payment_service.refund_payment(
            payment_id=payment_id,
            refund_data=refund_data,
        )
        
        return refund
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Refund processing failed: {str(e)}"
        )


@router.post("/payments/{payment_id}/verify", response_model=PaymentVerificationResponse)
async def verify_payment(
    payment_id: int,
    verification_data: PaymentVerificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Verify payment with additional authentication."""
    try:
        payment_service = PaymentService(db)
        await payment_service.initialize()
        
        # Set payment_id in verification request
        verification_data.payment_id = payment_id
        
        verification_response = await payment_service.verify_payment(verification_data)
        
        return verification_response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment verification failed: {str(e)}"
        )


@router.post("/webhooks/{gateway}")
async def process_webhook(
    gateway: str,
    webhook_data: dict,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Process incoming webhook from payment gateway."""
    try:
        payment_service = PaymentService(db)
        await payment_service.initialize()
        
        # Create webhook payload
        webhook_payload = PaymentWebhookPayload(
            gateway=gateway,
            event_type=webhook_data.get("type", "unknown"),
            event_id=webhook_data.get("id", ""),
            signature=request.headers.get("signature", ""),
            payload=webhook_data,
            received_at=datetime.utcnow(),
        )
        
        # Process webhook
        success = await payment_service.process_webhook(webhook_payload)
        
        if success:
            return {"status": "processed"}
        else:
            return {"status": "failed"}, status.HTTP_400_BAD_REQUEST
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )


@router.get("/payments/methods")
async def get_supported_payment_methods(
    db: AsyncSession = Depends(get_db),
):
    """Get list of supported payment methods."""
    try:
        payment_service = PaymentService(db)
        await payment_service.initialize()
        
        methods = []
        for gateway_name, gateway in payment_service._gateways.items():
            supported_methods = gateway.get_supported_payment_methods()
            methods.append({
                "gateway": gateway_name,
                "methods": [method.value for method in supported_methods],
                "currencies": gateway.get_supported_currencies(),
                "test_mode": gateway.is_test_mode(),
            })
        
        return {"payment_methods": methods}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve payment methods: {str(e)}"
        )


@router.get("/payments/health")
async def get_payment_health(
    db: AsyncSession = Depends(get_db),
):
    """Get health status of all payment gateways."""
    try:
        payment_service = PaymentService(db)
        await payment_service.initialize()
        
        health_status = await payment_service._router.get_gateway_metrics()
        
        return {"gateways": health_status}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve gateway health: {str(e)}"
        )


# Admin endpoints
@router.get("/admin/payments")
async def admin_get_payments(
    status: Optional[str] = None,
    gateway: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get payments with filtering (admin only)."""
    try:
        # Check admin permissions
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        payment_service = PaymentService(db)
        await payment_service.initialize()
        
        # Get payments based on filters
        if status:
            payments = await payment_service.repository.get_payments_by_status(status, limit)
        else:
            payments = await payment_service.repository.get_pending_payments(limit)
        
        return [PaymentResponse.from_orm(p) for p in payments]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve payments: {str(e)}"
        )


@router.get("/admin/payments/metrics")
async def admin_get_payment_metrics(
    gateway: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get payment metrics (admin only)."""
    try:
        # Check admin permissions
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        payment_service = PaymentService(db)
        await payment_service.initialize()
        
        metrics = await payment_service.repository.get_payment_metrics(
            gateway=gateway,
            start_date=start_date,
            end_date=end_date,
        )
        
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve metrics: {str(e)}"
        )
