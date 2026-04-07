from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.checkout import Cart, CartItem, Coupon, CouponProduct, Order, SavedItem
from app.models.operations import InventoryMovement, ShippingMethod, ShippingRateRule, TaxRule
from app.repositories.base import BaseRepository


class CheckoutRepository(BaseRepository):
    async def get_cart(self, cart_id: int) -> Cart | None:
        statement = (
            select(Cart)
            .options(selectinload(Cart.items))
            .where(Cart.id == cart_id)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_cart_by_session(self, session_key: str) -> Cart | None:
        statement = select(Cart).options(selectinload(Cart.items)).where(Cart.session_key == session_key)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_cart_item(self, cart_id: int, item_id: int) -> CartItem | None:
        result = await self.session.execute(select(CartItem).where(CartItem.cart_id == cart_id, CartItem.id == item_id))
        return result.scalar_one_or_none()

    async def list_saved_items(self, user_id: int) -> list[SavedItem]:
        result = await self.session.execute(select(SavedItem).where(SavedItem.user_id == user_id).order_by(SavedItem.created_at.desc()))
        return result.scalars().all()

    async def get_saved_item(self, user_id: int, item_id: int) -> SavedItem | None:
        result = await self.session.execute(select(SavedItem).where(SavedItem.user_id == user_id, SavedItem.id == item_id))
        return result.scalar_one_or_none()

    async def get_coupon_by_code(self, code: str) -> Coupon | None:
        statement = select(Coupon).options(selectinload(Coupon.products)).where(Coupon.code == code)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_coupons(self, page: int = 1, page_size: int = 20):
        return await self.paginate(select(Coupon).order_by(Coupon.created_at.desc()), page=page, page_size=page_size)

    async def get_coupon(self, coupon_id: int) -> Coupon | None:
        result = await self.session.execute(select(Coupon).options(selectinload(Coupon.products)).where(Coupon.id == coupon_id))
        return result.scalar_one_or_none()

    async def get_order(self, order_id: int) -> Order | None:
        statement = (
            select(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.addresses),
                selectinload(Order.shipment),
                selectinload(Order.status_history),
            )
            .where(Order.id == order_id)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_orders(
        self,
        *,
        user_id: int | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ):
        statement = (
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.addresses), selectinload(Order.shipment))
            .order_by(Order.created_at.desc())
        )
        if user_id is not None:
            statement = statement.where(Order.user_id == user_id)
        if status:
            statement = statement.where(Order.status == status)
        return await self.paginate(statement, page=page, page_size=page_size)

    async def list_shipping_methods(self) -> list[ShippingMethod]:
        result = await self.session.execute(select(ShippingMethod).where(ShippingMethod.is_enabled.is_(True)).order_by(ShippingMethod.name.asc()))
        return result.scalars().all()

    async def get_shipping_method_by_code(self, code: str) -> ShippingMethod | None:
        result = await self.session.execute(select(ShippingMethod).where(ShippingMethod.code == code))
        return result.scalar_one_or_none()

    async def list_shipping_rules(self, shipping_method_id: int | None = None) -> list[ShippingRateRule]:
        statement = select(ShippingRateRule).where(ShippingRateRule.is_active.is_(True))
        if shipping_method_id is not None:
            statement = statement.where(ShippingRateRule.shipping_method_id == shipping_method_id)
        result = await self.session.execute(statement.order_by(ShippingRateRule.id.asc()))
        return result.scalars().all()

    async def list_tax_rules(self) -> list[TaxRule]:
        result = await self.session.execute(select(TaxRule).where(TaxRule.is_active.is_(True)).order_by(TaxRule.id.asc()))
        return result.scalars().all()

    async def list_inventory_movements(self, page: int = 1, page_size: int = 50):
        return await self.paginate(select(InventoryMovement).order_by(InventoryMovement.created_at.desc()), page=page, page_size=page_size)
