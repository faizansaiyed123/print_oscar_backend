import logging
from datetime import timezone, datetime
from decimal import Decimal
from secrets import token_urlsafe

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.security import hash_password
from app.models.checkout import Cart, CartItem, CouponProduct, Order, OrderAddress, OrderItem, OrderShipment, OrderStatusHistory, SavedItem
from app.models.operations import InventoryMovement, ShippingRateRule, TaxRule
from app.models.user import Role, User
from app.repositories.catalog import CatalogRepository
from app.repositories.checkout import CheckoutRepository
from app.repositories.user import UserRepository
from app.schemas.checkout import CartCreate, CartItemCreate, CartItemUpdate, CheckoutRequest
from app.services.customization_resolver import CustomizationResolver


logger = logging.getLogger(__name__)


class CheckoutService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = CheckoutRepository(session)
        self.catalog = CatalogRepository(session)
        self.users = UserRepository(session)

    async def get_or_create_cart(self, payload: CartCreate, user_id: int | None = None) -> Cart:
        cart = None
        if payload.session_key:
            cart = await self.repository.get_cart_by_session(payload.session_key)
        if not cart:
            cart = Cart(
                user_id=user_id,
                session_key=payload.session_key or token_urlsafe(16),
                guest_email=payload.guest_email,
            )
            await self.repository.save(cart)
            await self.session.commit()
        return await self.get_cart(cart.id)

    async def get_cart(self, cart_id: int, coupon_code: str | None = None) -> Cart:
        cart = await self.repository.get_cart(cart_id)
        if not cart:
            raise AppException("Cart not found", 404)
        cart.totals = await self.calculate_totals(cart, coupon_code=coupon_code)
        return cart

    async def calculate_totals(self, cart: Cart, coupon_code: str | None = None) -> dict:
        """Calculate cart totals including discounts, shipping, and tax."""
        subtotal = sum(item.quantity * item.unit_price for item in cart.items)
        discount = Decimal("0.00")
        
        if coupon_code:
            coupon = await self.repository.get_coupon_by_code(coupon_code)
            if coupon and coupon.is_active:
                # Basic validation: min order amount
                if not coupon.min_order_amount or subtotal >= coupon.min_order_amount:
                    if coupon.discount_type == "percentage":
                        discount = (subtotal * coupon.discount_value / 100).quantize(Decimal("0.01"))
                    else:
                        discount = min(coupon.discount_value, subtotal)

        # Shipping and Tax placeholders for Cart view
        shipping = Decimal("0.00")
        tax = Decimal("0.00")
        total = subtotal - discount + shipping + tax
        
        return {
            "subtotal": subtotal,
            "discount": discount,
            "shipping": shipping,
            "tax": tax,
            "total": max(Decimal("0.00"), total),
            "coupon_code": coupon_code if discount > 0 else None
        }

    def _calculate_shipping_amount(self, base_rate: Decimal, rules: list, subtotal: Decimal, state: str, zip_code: str, country: str = "US") -> Decimal:
        """Helper to calculate shipping based on matching rules."""
        amount = base_rate
        for rule in rules:
            if rule.country_code and rule.country_code != country:
                continue
            if rule.state and rule.state != state:
                continue
            if rule.min_order_amount and subtotal < rule.min_order_amount:
                continue
            # If we match, add the extra charge
            amount += rule.extra_charge
            break
        return amount

    async def add_cart_item(self, cart_id: int, payload: CartItemCreate) -> Cart:
        cart = await self.repository.get_cart(cart_id)
        if not cart:
            raise AppException("Cart not found", 404)

        product = await self.catalog.get_product(payload.product_id)

        # Check stock status instead of quantity
        if product.stock_status != "instock":
            raise AppException("Product is out of stock", 400)

        # Resolve all rules (DB + Category Inheritance)
        resolved_rules = await CustomizationResolver.resolve_rules(product, self.session)

        # Validate customization rules
        payload_data = payload.customization_payload or {}
        for rule in resolved_rules:
            if not rule.is_enabled:
                continue

            value = payload_data.get(rule.label) or payload_data.get(rule.field_type)

            if rule.is_required and not value:
                raise AppException(f"Customization field '{rule.label}' is required", 400)

            if value and rule.validation_rules:
                v_rules = rule.validation_rules
                if isinstance(value, str):
                    if "min_length" in v_rules and len(value) < v_rules["min_length"]:
                        raise AppException(f"Field '{rule.label}' must be at least {v_rules['min_length']} characters", 400)
                    if "max_length" in v_rules and len(value) > v_rules["max_length"]:
                        raise AppException(f"Field '{rule.label}' cannot exceed {v_rules['max_length']} characters", 400)

                if "options" in v_rules and isinstance(v_rules["options"], list):
                    if value not in v_rules["options"]:
                        raise AppException(
                            f"Invalid option for '{rule.label}'. Must be one of: {', '.join(map(str, v_rules['options']))}",
                            400
                        )

        unit_price = product.price
        if payload.variant_id:
            variant = next((v for v in product.variants if v.id == payload.variant_id), None)
            if not variant:
                raise AppException("Variant not found", 404)
            if variant.stock_status != "instock":
                raise AppException("Variant is out of stock", 400)
            if variant.price_override is not None:
                unit_price = variant.price_override

        existing_item = next(
            (
                item
                for item in cart.items
                if item.product_id == payload.product_id and item.variant_id == payload.variant_id
            ),
            None,
        )

        if existing_item:
            existing_item.quantity += payload.quantity
            existing_item.customization_payload = payload.customization_payload
        else:
            cart.items.append(
                CartItem(
                    product_id=payload.product_id,
                    variant_id=payload.variant_id,
                    quantity=payload.quantity,
                    unit_price=unit_price,
                    customization_payload=payload.customization_payload,
                )
            )

        await self.session.commit()
        return await self.get_cart(cart_id)

    async def update_cart_item(self, cart_id: int, item_id: int, payload: CartItemUpdate) -> Cart:
        item = await self.repository.get_cart_item(cart_id, item_id)
        if not item:
            raise AppException("Cart item not found", 404)
        item.quantity = payload.quantity
        item.customization_payload = payload.customization_payload
        await self.session.commit()
        return await self.get_cart(cart_id)

    async def remove_cart_item(self, cart_id: int, item_id: int) -> Cart:
        item = await self.repository.get_cart_item(cart_id, item_id)
        if not item:
            raise AppException("Cart item not found", 404)
        await self.repository.delete(item)
        await self.session.commit()
        return await self.get_cart(cart_id)

    async def save_for_later(self, user_id: int, item_id: int, cart_id: int) -> SavedItem:
        item = await self.repository.get_cart_item(cart_id, item_id)
        if not item:
            raise AppException("Cart item not found", 404)
        saved = SavedItem(user_id=user_id, product_id=item.product_id, variant_id=item.variant_id)
        await self.repository.save(saved)
        await self.repository.delete(item)
        await self.session.commit()
        return saved

    async def list_saved_items(self, user_id: int) -> list[SavedItem]:
        return await self.repository.list_saved_items(user_id)

    async def remove_saved_item(self, user_id: int, item_id: int) -> None:
        item = await self.repository.get_saved_item(user_id, item_id)
        if not item:
            raise AppException("Saved item not found", 404)
        await self.repository.delete(item)
        await self.session.commit()

    async def apply_coupon(self, cart_id: int, coupon_code: str):
        cart = await self.get_cart(cart_id)
        cart.totals = await self.calculate_totals(cart, coupon_code=coupon_code)
        return cart.totals

    async def quote_shipping(self, cart_id: int, state: str, zip_code: str, country_code: str = "US") -> list[dict]:
        cart = await self.get_cart(cart_id)
        methods = await self.repository.list_shipping_methods()
        quotes = []
        for method in methods:
            shipping_amount = self._calculate_shipping_amount(
                method.base_rate,
                await self.repository.list_shipping_rules(method.id),
                cart.totals["subtotal"],
                state,
                zip_code,
                country_code,
            )
            quotes.append(
                {
                    "code": method.code,
                    "name": method.name,
                    "estimated_days": method.estimated_days,
                    "amount": shipping_amount,
                }
            )
        return quotes

    async def checkout(self, user_id: int | None, payload: CheckoutRequest) -> Order:
        logger.info(f"Starting checkout for cart {payload.cart_id}, user {user_id}")
        cart = await self.repository.get_cart(payload.cart_id)
        if not cart:
            logger.error(f"Cart {payload.cart_id} not found")
            raise AppException("Cart not found", 404)
        if not cart.items:
            logger.error(f"Cart {payload.cart_id} has no items")
            raise AppException("Cart is empty", 400)

        # 1. Total calculation
        totals = await self.calculate_totals(cart, coupon_code=payload.coupon_code)
        
        shipping_method = None
        if payload.shipping_method:
            shipping_method = await self.repository.get_shipping_method_by_code(payload.shipping_method)
            
        if not shipping_method:
            logger.warning(f"Invalid or missing shipping method: '{payload.shipping_method}'. Falling back to first available.")
            methods = await self.repository.list_shipping_methods()
            if not methods:
                logger.error("No shipping methods available in the database.")
                raise AppException("No shipping methods available in the database", 400)
            shipping_method = methods[0]
            logger.info(f"Using fallback shipping method: {shipping_method.code}")
            
        shipping_amount = self._calculate_shipping_amount(
            shipping_method.base_rate,
            await self.repository.list_shipping_rules(shipping_method.id),
            totals["subtotal"],
            payload.shipping_address.state,
            payload.shipping_address.zip_code,
            payload.shipping_address.country_code,
        )
        
        # Simple tax calculation placeholder (e.g., 0% for now or could fetch TaxRules)
        tax_amount = Decimal("0.00")
        total_amount = totals["subtotal"] - totals["discount"] + shipping_amount + tax_amount

        # 2. Handle account creation for guests
        if not user_id and payload.create_account:
            existing_user = await self.users.get_by_email(payload.shipping_address.email)
            if existing_user:
                if not existing_user.is_guest:
                    raise AppException("An account with this email already exists", 400)
                user_id = existing_user.id
            else:
                new_user = User(
                    email=payload.shipping_address.email,
                    first_name=payload.shipping_address.first_name,
                    last_name=payload.shipping_address.last_name,
                    password_hash=hash_password(payload.account_password) if payload.account_password else None,
                    is_guest=False,
                    is_active=True
                )
                roles = await self.users.list_roles()
                customer_role = next((r for r in roles if r.name == "Customer"), None)
                if customer_role:
                    new_user.roles.append(customer_role)
                
                await self.repository.save(new_user)
                await self.session.flush()
                user_id = new_user.id

        # 3. Create Order
        order_number = f"ORD-{token_urlsafe(8).upper()}"
        order = Order(
            user_id=user_id,
            order_number=order_number,
            status="pending",
            payment_status="pending",
            payment_method=payload.payment_method,
            shipping_status="pending",
            currency_code=cart.currency_code,
            subtotal_amount=totals["subtotal"],
            discount_amount=totals["discount"],
            shipping_amount=shipping_amount,
            tax_amount=tax_amount,
            total_amount=total_amount,
            coupon_code=totals["coupon_code"],
            notes=payload.notes
        )
        await self.repository.save(order)
        await self.session.flush()

        # 4. Create Addresses
        shipping_addr = OrderAddress(
            order_id=order.id,
            address_type="shipping",
            **payload.shipping_address.model_dump()
        )
        billing_addr = OrderAddress(
            order_id=order.id,
            address_type="billing",
            **payload.billing_address.model_dump()
        )
        await self.repository.save(shipping_addr)
        await self.repository.save(billing_addr)

        # 5. Create Order Items & Update Inventory
        for cart_item in cart.items:
            product = await self.catalog.get_product(cart_item.product_id)
            if not product:
                continue
                
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                variant_id=cart_item.variant_id,
                product_title=product.title,
                sku=product.sku,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                total_price=cart_item.unit_price * cart_item.quantity,
                customization_payload=cart_item.customization_payload
            )
            
            # Stock update
            if cart_item.variant_id:
                variant = next((v for v in product.variants if v.id == cart_item.variant_id), None)
                if variant:
                    order_item.sku = variant.sku or product.sku
                    variant.stock_quantity -= cart_item.quantity
                    await self.repository.save(InventoryMovement(
                        product_id=product.id,
                        variant_id=variant.id,
                        movement_type="sale",
                        quantity_delta=-cart_item.quantity,
                        balance_after=variant.stock_quantity,
                        reason=f"Order {order_number}"
                    ))
            else:
                product.stock_quantity -= cart_item.quantity
                await self.repository.save(InventoryMovement(
                    product_id=product.id,
                    movement_type="sale",
                    quantity_delta=-cart_item.quantity,
                    balance_after=product.stock_quantity,
                    reason=f"Order {order_number}"
                ))
            
            await self.repository.save(order_item)

        # 6. Status History
        history = OrderStatusHistory(
            order_id=order.id,
            status="pending",
            notes="Order placement started",
            created_at=datetime.now(timezone.utc)
        )
        await self.repository.save(history)

        # 7. Clear Cart
        for item in cart.items:
            await self.session.delete(item)
        await self.session.delete(cart)

        await self.session.commit()
        return await self.repository.get_order(order.id)