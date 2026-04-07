from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.security import hash_password
from app.models.checkout import Coupon, CouponProduct
from app.models.catalog import Product, ProductVariant
from app.models.operations import InventoryMovement, RedirectRule, ShippingMethod, ShippingRateRule, TaxRule
from app.models.settings import Banner, Campaign, NewsletterSubscriber, StoreSetting
from app.repositories.admin import AdminRepository
from app.repositories.checkout import CheckoutRepository
from app.repositories.user import UserRepository
from app.schemas.admin import (
    BannerWrite,
    CampaignWrite,
    CouponWrite,
    InventoryAdjustmentWrite,
    RedirectRuleWrite,
    ShippingMethodWrite,
    ShippingRateRuleWrite,
    StoreSettingWrite,
    TaxRuleWrite,
)
from app.services.user import UserService


class AdminService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = AdminRepository(session)
        self.checkout = CheckoutRepository(session)
        self.users = UserRepository(session)
        self.user_service = UserService(session)

    async def dashboard(self):
        return await self.repository.dashboard_metrics()

    async def sales_report(self):
        return await self.repository.sales_report()

    async def customer_growth_report(self):
        return await self.repository.customer_growth_report()

    async def product_performance_report(self):
        return await self.repository.product_performance_report()

    async def list_settings(self):
        return await self.repository.list_settings()

    async def upsert_setting(self, payload: StoreSettingWrite) -> StoreSetting:
        setting = await self.repository.get_setting(payload.key)
        if setting:
            setting.value = payload.value
            setting.is_public = payload.is_public
        else:
            setting = StoreSetting(key=payload.key, value=payload.value, is_public=payload.is_public)
            await self.repository.save(setting)
        await self.session.commit()
        return setting

    async def list_banners(self):
        return await self.repository.list_banners()

    async def create_banner(self, payload: BannerWrite) -> Banner:
        banner = Banner(**payload.model_dump())
        await self.repository.save(banner)
        await self.session.commit()
        return banner

    async def update_banner(self, banner_id: int, payload: BannerWrite) -> Banner:
        banner = await self.repository.get_banner(banner_id)
        if not banner:
            raise AppException("Banner not found", 404)
        for field, value in payload.model_dump().items():
            setattr(banner, field, value)
        await self.session.commit()
        return banner

    async def delete_banner(self, banner_id: int) -> None:
        banner = await self.repository.get_banner(banner_id)
        if not banner:
            raise AppException("Banner not found", 404)
        await self.repository.delete(banner)
        await self.session.commit()

    async def list_campaigns(self):
        return await self.repository.list_campaigns()

    async def create_campaign(self, payload: CampaignWrite) -> Campaign:
        campaign = Campaign(**payload.model_dump())
        await self.repository.save(campaign)
        await self.session.commit()
        return campaign

    async def update_campaign(self, campaign_id: int, payload: CampaignWrite) -> Campaign:
        campaign = await self.repository.get_campaign(campaign_id)
        if not campaign:
            raise AppException("Campaign not found", 404)
        for field, value in payload.model_dump().items():
            setattr(campaign, field, value)
        await self.session.commit()
        return campaign

    async def delete_campaign(self, campaign_id: int) -> None:
        campaign = await self.repository.get_campaign(campaign_id)
        if not campaign:
            raise AppException("Campaign not found", 404)
        await self.repository.delete(campaign)
        await self.session.commit()

    async def dispatch_campaign(self, campaign_id: int) -> dict[str, str | int]:
        campaign = await self.repository.get_campaign(campaign_id)
        if not campaign:
            raise AppException("Campaign not found", 404)
        recipients = await self.repository.list_newsletter_subscribers()
        await self.repository.create_activity_log(
            action="campaign_dispatch",
            entity_type="campaign",
            entity_id=campaign.id,
            details=f"Queued for {len(recipients)} recipients",
        )
        await self.session.commit()
        return {"message": "Campaign queued for dispatch", "recipient_count": len(recipients)}

    async def subscribe_newsletter(self, email: str) -> NewsletterSubscriber:
        subscribers = await self.repository.list_newsletter_subscribers()
        existing = next((subscriber for subscriber in subscribers if subscriber.email.lower() == email.lower()), None)
        if existing:
            existing.is_active = True
            await self.session.commit()
            return existing
        subscriber = NewsletterSubscriber(email=email, is_active=True)
        await self.repository.save(subscriber)
        await self.session.commit()
        return subscriber

    async def list_shipping_methods(self):
        return await self.repository.list_shipping_methods()

    async def create_shipping_method(self, payload: ShippingMethodWrite) -> ShippingMethod:
        method = ShippingMethod(**payload.model_dump())
        await self.repository.save(method)
        await self.session.commit()
        return method

    async def update_shipping_method(self, method_id: int, payload: ShippingMethodWrite) -> ShippingMethod:
        method = await self.repository.get_shipping_method(method_id)
        if not method:
            raise AppException("Shipping method not found", 404)
        for field, value in payload.model_dump().items():
            setattr(method, field, value)
        await self.session.commit()
        return method

    async def delete_shipping_method(self, method_id: int) -> None:
        method = await self.repository.get_shipping_method(method_id)
        if not method:
            raise AppException("Shipping method not found", 404)
        await self.repository.delete(method)
        await self.session.commit()

    async def list_shipping_rules(self):
        return await self.repository.list_shipping_rules()

    async def create_shipping_rule(self, payload: ShippingRateRuleWrite) -> ShippingRateRule:
        rule = ShippingRateRule(**payload.model_dump())
        await self.repository.save(rule)
        await self.session.commit()
        return rule

    async def update_shipping_rule(self, rule_id: int, payload: ShippingRateRuleWrite) -> ShippingRateRule:
        rule = await self.repository.get_shipping_rule(rule_id)
        if not rule:
            raise AppException("Shipping rule not found", 404)
        for field, value in payload.model_dump().items():
            setattr(rule, field, value)
        await self.session.commit()
        return rule

    async def delete_shipping_rule(self, rule_id: int) -> None:
        rule = await self.repository.get_shipping_rule(rule_id)
        if not rule:
            raise AppException("Shipping rule not found", 404)
        await self.repository.delete(rule)
        await self.session.commit()

    async def list_tax_rules(self):
        return await self.repository.list_tax_rules()

    async def create_tax_rule(self, payload: TaxRuleWrite) -> TaxRule:
        rule = TaxRule(**payload.model_dump())
        await self.repository.save(rule)
        await self.session.commit()
        return rule

    async def update_tax_rule(self, tax_rule_id: int, payload: TaxRuleWrite) -> TaxRule:
        rule = await self.repository.get_tax_rule(tax_rule_id)
        if not rule:
            raise AppException("Tax rule not found", 404)
        for field, value in payload.model_dump().items():
            setattr(rule, field, value)
        await self.session.commit()
        return rule

    async def delete_tax_rule(self, tax_rule_id: int) -> None:
        rule = await self.repository.get_tax_rule(tax_rule_id)
        if not rule:
            raise AppException("Tax rule not found", 404)
        await self.repository.delete(rule)
        await self.session.commit()

    async def list_inventory_movements(self, page: int = 1, page_size: int = 50):
        return await self.repository.list_inventory_movements(page=page, page_size=page_size)

    async def adjust_inventory(self, payload: InventoryAdjustmentWrite, admin_user_id: int | None = None) -> InventoryMovement:
        if payload.variant_id is not None:
            variant = await self.session.get(ProductVariant, payload.variant_id)
            if not variant:
                raise AppException("Variant not found", 404)
            variant.stock_quantity += payload.quantity_delta
            balance_after = variant.stock_quantity
        else:
            product = await self.session.get(Product, payload.product_id)
            if not product:
                raise AppException("Product not found", 404)
            product.stock_quantity += payload.quantity_delta
            if product.stock_quantity <= 0:
                product.stock_status = "out_of_stock"
            elif product.stock_quantity <= 5:
                product.stock_status = "low_stock"
            else:
                product.stock_status = "in_stock"
            balance_after = product.stock_quantity

        movement = InventoryMovement(
            product_id=payload.product_id,
            variant_id=payload.variant_id,
            warehouse_name=payload.warehouse_name,
            movement_type=payload.movement_type,
            quantity_delta=payload.quantity_delta,
            balance_after=balance_after,
            reason=payload.reason,
            created_by_user_id=admin_user_id,
        )
        await self.repository.save(movement)
        await self.session.commit()
        return movement

    async def list_redirects(self):
        return await self.repository.list_redirects()

    async def create_redirect(self, payload: RedirectRuleWrite) -> RedirectRule:
        redirect = RedirectRule(**payload.model_dump())
        await self.repository.save(redirect)
        await self.session.commit()
        return redirect

    async def update_redirect(self, redirect_id: int, payload: RedirectRuleWrite) -> RedirectRule:
        redirect = await self.repository.get_redirect(redirect_id)
        if not redirect:
            raise AppException("Redirect not found", 404)
        for field, value in payload.model_dump().items():
            setattr(redirect, field, value)
        await self.session.commit()
        return redirect

    async def delete_redirect(self, redirect_id: int) -> None:
        redirect = await self.repository.get_redirect(redirect_id)
        if not redirect:
            raise AppException("Redirect not found", 404)
        await self.repository.delete(redirect)
        await self.session.commit()

    async def list_roles(self):
        return await self.repository.list_roles()

    async def list_permissions(self):
        return await self.users.list_permissions()

    async def create_role(self, name: str, description: str | None, permission_ids: list[int]):
        return await self.user_service.create_role(name, description, permission_ids)

    async def update_role(self, role_id: int, name: str | None, description: str | None, permission_ids: list[int] | None):
        return await self.user_service.update_role(role_id, name, description, permission_ids)

    async def create_admin_user(self, payload) -> object:
        return await self.user_service.create_admin_user(
            email=payload.email,
            password_hash=hash_password(payload.password),
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone_number=payload.phone_number,
            role_ids=payload.role_ids,
        )

    async def send_email_to_customer(self, customer_id: int, subject: str, body: str) -> dict[str, str]:
        customer = await self.users.get_by_id(customer_id)
        if not customer:
            raise AppException("Customer not found", 404)
        await self.repository.create_activity_log(
            action="send_email",
            entity_type="user",
            entity_id=customer_id,
            details=f"subject={subject}\n{body}",
        )
        await self.session.commit()
        return {"message": f"Email queued for {customer.email}"}

    async def list_activity_logs(self, page: int = 1, page_size: int = 50):
        return await self.repository.list_activity_logs(page=page, page_size=page_size)

    async def list_coupons(self, page: int = 1, page_size: int = 20):
        return await self.repository.list_coupons(page=page, page_size=page_size)

    async def create_coupon(self, payload: CouponWrite) -> Coupon:
        coupon = Coupon(
            code=payload.code,
            description=payload.description,
            discount_type=payload.discount_type,
            discount_value=payload.discount_value,
            starts_at=payload.starts_at,
            expires_at=payload.expires_at,
            usage_limit=payload.usage_limit,
            min_order_amount=payload.min_order_amount,
            applies_to_all_products=payload.applies_to_all_products,
            is_active=payload.is_active,
        )
        await self.checkout.save(coupon)
        if not payload.applies_to_all_products:
            coupon.products = [CouponProduct(product_id=product_id) for product_id in payload.product_ids]
        await self.session.commit()
        return coupon

    async def update_coupon(self, coupon_id: int, payload: CouponWrite) -> Coupon:
        coupon = await self.checkout.get_coupon(coupon_id)
        if not coupon:
            raise AppException("Coupon not found", 404)
        for field, value in payload.model_dump(exclude={"product_ids"}).items():
            setattr(coupon, field, value)
        coupon.products = [CouponProduct(product_id=product_id) for product_id in payload.product_ids]
        await self.session.commit()
        return coupon

    async def delete_coupon(self, coupon_id: int) -> None:
        coupon = await self.checkout.get_coupon(coupon_id)
        if not coupon:
            raise AppException("Coupon not found", 404)
        await self.checkout.delete(coupon)
        await self.session.commit()
