from datetime import timezone, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.catalog import Product, ProductVariant
from app.models.checkout import Order, OrderStatusHistory
from app.models.operations import InventoryMovement
from app.repositories.checkout import CheckoutRepository
from app.utils.files import ensure_storage_path, safe_relative_storage_path


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = CheckoutRepository(session)

    async def list_orders(self, user_id: int, page: int = 1, page_size: int = 20):
        return await self.repository.list_orders(user_id=user_id, page=page, page_size=page_size)

    async def get_order(self, order_id: int, user_id: int | None = None) -> Order:
        order = await self.repository.get_order(order_id)
        if not order:
            raise AppException("Order not found", 404)
        if user_id is not None and order.user_id != user_id:
            raise AppException("Order not found", 404)
        return order

    async def cancel_order(self, order_id: int, *, user_id: int | None = None, reason: str | None = None) -> Order:
        order = await self.get_order(order_id, user_id=user_id)
        if order.status not in {"pending", "placed", "processing"}:
            raise AppException("Order can no longer be cancelled", 400)
        order.status = "cancelled"
        order.payment_status = "cancelled"
        order.shipping_status = "cancelled"
        order.cancellation_reason = reason
        order.status_history.append(
            OrderStatusHistory(status="cancelled", notes=reason or "Cancelled by customer", created_at=datetime.now(timezone.utc))
        )
        await self._restore_inventory(order)
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def admin_update_order(self, order_id: int, payload: dict) -> Order:
        order = await self.get_order(order_id)
        previous_status = order.status
        notes = []
        if payload.get("status") is not None:
            order.status = payload["status"]
            notes.append(f"status={payload['status']}")
        if payload.get("payment_status") is not None:
            order.payment_status = payload["payment_status"]
            notes.append(f"payment_status={payload['payment_status']}")
        if payload.get("shipping_status") is not None:
            order.shipping_status = payload["shipping_status"]
            notes.append(f"shipping_status={payload['shipping_status']}")
        if payload.get("tracking_number") is not None:
            order.tracking_number = payload["tracking_number"]
            if order.shipment:
                order.shipment.tracking_number = payload["tracking_number"]
        if payload.get("cancellation_reason"):
            order.cancellation_reason = payload["cancellation_reason"]
        if payload.get("refund_amount") is not None:
            refund_amount = Decimal(str(payload["refund_amount"]))
            order.refunded_amount += refund_amount
            order.payment_status = "refunded"
            notes.append(f"refund_amount={refund_amount}")
            await self._restore_inventory(order)
        elif previous_status != "cancelled" and order.status == "cancelled":
            await self._restore_inventory(order)

        order.status_history.append(
            OrderStatusHistory(
                status=order.status,
                notes=payload.get("notes") or ", ".join(notes) or "Order updated",
                created_at=datetime.now(timezone.utc),
            )
        )
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def track_order(self, order_id: int, user_id: int | None = None) -> dict:
        order = await self.get_order(order_id, user_id=user_id)
        return {
            "order_number": order.order_number,
            "status": order.status,
            "shipping_status": order.shipping_status,
            "tracking_number": order.tracking_number or (order.shipment.tracking_number if order.shipment else None),
        }

    async def generate_invoice(self, order_id: int, user_id: int | None = None) -> str:
        order = await self.get_order(order_id, user_id=user_id)
        billing = next((address for address in order.addresses if address.address_type == "billing"), None)
        lines = [
            f"Invoice for {order.order_number}",
            f"Status: {order.status}",
            f"Payment: {order.payment_status}",
            "",
            "Billing Address:",
            f"{billing.first_name} {billing.last_name}" if billing else "N/A",
            f"{billing.street_address}, {billing.city}, {billing.state} {billing.zip_code}" if billing else "",
            "",
            "Items:",
        ]
        for item in order.items:
            lines.append(f"- {item.product_title} x{item.quantity} @ {item.unit_price} = {item.total_price}")
        lines.extend(
            [
                "",
                f"Subtotal: {order.subtotal_amount}",
                f"Discount: {order.discount_amount}",
                f"Shipping: {order.shipping_amount}",
                f"Tax: {order.tax_amount}",
                f"Total: {order.total_amount}",
            ]
        )
        content = "\n".join(lines)
        file_path = ensure_storage_path("invoices", f"{order.order_number}.txt")
        file_path.write_text(content, encoding="utf-8")
        return safe_relative_storage_path(str(file_path))

    async def generate_shipping_label(self, order_id: int) -> str:
        order = await self.get_order(order_id)
        shipping = next((address for address in order.addresses if address.address_type == "shipping"), None)
        if not shipping:
            raise AppException("Shipping address unavailable", 400)
        content = "\n".join(
            [
                f"Shipping Label for {order.order_number}",
                f"{shipping.first_name} {shipping.last_name}",
                shipping.street_address,
                shipping.apartment or "",
                f"{shipping.city}, {shipping.state} {shipping.zip_code}",
                shipping.country_code,
                f"Tracking: {order.tracking_number or 'Pending'}",
            ]
        )
        file_path = ensure_storage_path("labels", f"{order.order_number}.txt")
        file_path.write_text(content, encoding="utf-8")
        if order.shipment:
            order.shipment.label_url = safe_relative_storage_path(str(file_path))
            await self.session.commit()
        return safe_relative_storage_path(str(file_path))

    async def _restore_inventory(self, order: Order) -> None:
        for item in order.items:
            if item.product_id is None:
                continue
            if item.variant_id is not None:
                variant = await self.session.get(ProductVariant, item.variant_id)
                if variant:
                    variant.stock_quantity += item.quantity
            else:
                product = await self.session.get(Product, item.product_id)
                if product:
                    product.stock_quantity += item.quantity
                    if product.stock_quantity <= 0:
                        product.stock_status = "out_of_stock"
                    elif product.stock_quantity <= 5:
                        product.stock_status = "low_stock"
                    else:
                        product.stock_status = "in_stock"
            self.session.add(
                InventoryMovement(
                    product_id=item.product_id,
                    variant_id=item.variant_id,
                    movement_type="refund",
                    quantity_delta=item.quantity,
                    reason=f"Order {order.order_number} cancelled/refunded",
                )
            )
