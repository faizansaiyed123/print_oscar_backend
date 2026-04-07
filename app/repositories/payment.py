"""Payment repository for database operations."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.payment import (
    Payment,
    PaymentMethodDetails,
    PaymentRefund,
    PaymentTransaction,
)


class PaymentRepository:
    """Repository for payment-related database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_payment(self, payment: Payment) -> Payment:
        """Create a new payment."""
        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)
        return payment
    
    async def get_payment(self, payment_id: int) -> Optional[Payment]:
        """Get payment by ID."""
        stmt = select(Payment).options(
            selectinload(Payment.transactions),
            selectinload(Payment.refunds),
            selectinload(Payment.method_details),
        ).where(Payment.id == payment_id)
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_payment_by_gateway_id(
        self, 
        gateway: str, 
        gateway_payment_id: str
    ) -> Optional[Payment]:
        """Get payment by gateway and gateway payment ID."""
        stmt = select(Payment).options(
            selectinload(Payment.transactions),
            selectinload(Payment.refunds),
            selectinload(Payment.method_details),
        ).where(
            Payment.payment_gateway == gateway,
            Payment.gateway_payment_id == gateway_payment_id,
        )
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_payments_by_order(self, order_id: int) -> List[Payment]:
        """Get all payments for an order."""
        stmt = select(Payment).options(
            selectinload(Payment.transactions),
            selectinload(Payment.refunds),
        ).where(Payment.order_id == order_id)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def update_payment(self, payment: Payment) -> Payment:
        """Update payment."""
        await self.db.commit()
        await self.db.refresh(payment)
        return payment
    
    async def create_payment_method_details(
        self, 
        method_details: PaymentMethodDetails
    ) -> PaymentMethodDetails:
        """Create payment method details."""
        self.db.add(method_details)
        await self.db.commit()
        await self.db.refresh(method_details)
        return method_details
    
    async def create_transaction(self, transaction: PaymentTransaction) -> PaymentTransaction:
        """Create payment transaction."""
        self.db.add(transaction)
        await self.db.commit()
        await self.db.refresh(transaction)
        return transaction
    
    async def get_payment_transactions(self, payment_id: int) -> List[PaymentTransaction]:
        """Get all transactions for a payment."""
        stmt = select(PaymentTransaction).where(
            PaymentTransaction.payment_id == payment_id
        ).order_by(PaymentTransaction.created_at.desc())
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def create_refund(self, refund: PaymentRefund) -> PaymentRefund:
        """Create payment refund."""
        self.db.add(refund)
        await self.db.commit()
        await self.db.refresh(refund)
        return refund
    
    async def get_payment_refunds(self, payment_id: int) -> List[PaymentRefund]:
        """Get all refunds for a payment."""
        stmt = select(PaymentRefund).where(
            PaymentRefund.payment_id == payment_id
        ).order_by(PaymentRefund.created_at.desc())
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_refund_by_gateway_id(
        self, 
        gateway: str, 
        gateway_refund_id: str
    ) -> Optional[PaymentRefund]:
        """Get refund by gateway refund ID."""
        stmt = select(PaymentRefund).join(Payment).where(
            Payment.payment_gateway == gateway,
            PaymentRefund.gateway_refund_id == gateway_refund_id,
        )
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_pending_payments(self, limit: int = 100) -> List[Payment]:
        """Get payments that are pending and may need attention."""
        stmt = select(Payment).where(
            Payment.status.in_(["pending", "processing"])
        ).order_by(Payment.created_at).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_payments_by_status(
        self, 
        status: str, 
        limit: int = 100
    ) -> List[Payment]:
        """Get payments by status."""
        stmt = select(Payment).where(
            Payment.status == status
        ).order_by(Payment.created_at.desc()).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_payments_by_customer(
        self, 
        customer_email: str, 
        limit: int = 50
    ) -> List[Payment]:
        """Get payments for a customer."""
        stmt = select(Payment).where(
            Payment.customer_email == customer_email
        ).order_by(Payment.created_at.desc()).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_payment_metrics(
        self, 
        gateway: Optional[str] = None,
        start_date: Optional = None,
        end_date: Optional = None
    ) -> dict:
        """Get payment metrics for reporting."""
        # This is a simplified version - in production you'd want more sophisticated queries
        from sqlalchemy import func, and_
        from app.models.payment import PaymentStatus
        
        base_query = select(Payment)
        conditions = []
        
        if gateway:
            conditions.append(Payment.payment_gateway == gateway)
        
        if start_date:
            conditions.append(Payment.created_at >= start_date)
        
        if end_date:
            conditions.append(Payment.created_at <= end_date)
        
        if conditions:
            base_query = base_query.where(and_(*conditions))
        
        # Get counts by status
        status_counts = {}
        for status in PaymentStatus:
            stmt = select(func.count(Payment.id)).where(
                Payment.status == status.value,
                *conditions
            )
            result = await self.db.execute(stmt)
            status_counts[status.value] = result.scalar() or 0
        
        # Get total amounts
        total_stmt = select(
            func.sum(Payment.amount),
            func.count(Payment.id)
        ).where(*conditions)
        total_result = await self.db.execute(total_stmt)
        total_amount, total_count = total_result.first()
        
        return {
            "total_payments": total_count or 0,
            "total_amount": total_amount or 0,
            "status_breakdown": status_counts,
        }
