from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models.audit import AdminActivityLog
from app.models.catalog import Product, ProductMeta, ProductReview
from app.models.media import MediaAsset, UploadedCustomerFile
from app.models.operations import InventoryMovement, RedirectRule, ShippingMethod, ShippingRateRule, TaxRule
from app.models.settings import Banner, Campaign, NewsletterSubscriber, StoreSetting
from app.models.checkout import Coupon, Order, OrderItem
from app.models.user import Role, User
from app.repositories.base import BaseRepository


class AdminRepository(BaseRepository):
    async def dashboard_metrics(self):
        total_sales = await self.session.scalar(select(func.coalesce(func.sum(Order.total_amount), 0)))
        total_orders = await self.session.scalar(select(func.count()).select_from(Order))
        total_customers = await self.session.scalar(select(func.count()).select_from(User).where(User.is_guest.is_(False)))
        low_stock_products = await self.session.scalar(
            select(func.count())
            .select_from(Product)
            .outerjoin(ProductMeta, ProductMeta.product_id == Product.id)
            .where(Product.stock_quantity <= func.coalesce(ProductMeta.low_stock_threshold, 5))
        )
        return {
            "total_sales": total_sales or 0,
            "total_orders": int(total_orders or 0),
            "total_customers": int(total_customers or 0),
            "low_stock_products": int(low_stock_products or 0),
        }

    async def sales_report(self):
        statement = (
            select(func.date(Order.created_at).label("period"), func.coalesce(func.sum(Order.total_amount), 0).label("revenue"), func.count(Order.id).label("orders"))
            .group_by(func.date(Order.created_at))
            .order_by(func.date(Order.created_at).desc())
        )
        result = await self.session.execute(statement)
        return [
            {"period": str(row.period), "revenue": row.revenue, "orders": int(row.orders)}
            for row in result.all()
        ]

    async def customer_growth_report(self):
        statement = (
            select(func.date(User.created_at).label("period"), func.count(User.id).label("customers"))
            .where(User.is_guest.is_(False))
            .group_by(func.date(User.created_at))
            .order_by(func.date(User.created_at).desc())
        )
        result = await self.session.execute(statement)
        return [{"period": str(row.period), "customers": int(row.customers)} for row in result.all()]

    async def product_performance_report(self):
        statement = (
            select(
                OrderItem.product_title.label("product_title"),
                func.coalesce(func.sum(OrderItem.quantity), 0).label("units_sold"),
                func.coalesce(func.sum(OrderItem.total_price), 0).label("revenue"),
            )
            .group_by(OrderItem.product_title)
            .order_by(func.coalesce(func.sum(OrderItem.total_price), 0).desc())
        )
        result = await self.session.execute(statement)
        return [
            {
                "product_title": row.product_title,
                "units_sold": int(row.units_sold),
                "revenue": row.revenue,
            }
            for row in result.all()
        ]

    async def list_settings(self) -> list[StoreSetting]:
        result = await self.session.execute(select(StoreSetting).order_by(StoreSetting.key.asc()))
        return result.scalars().all()

    async def get_setting(self, key: str) -> StoreSetting | None:
        result = await self.session.execute(select(StoreSetting).where(StoreSetting.key == key))
        return result.scalar_one_or_none()

    async def list_banners(self) -> list[Banner]:
        result = await self.session.execute(select(Banner).order_by(Banner.created_at.desc()))
        return result.scalars().all()

    async def get_banner(self, banner_id: int) -> Banner | None:
        result = await self.session.execute(select(Banner).where(Banner.id == banner_id))
        return result.scalar_one_or_none()

    async def list_campaigns(self) -> list[Campaign]:
        result = await self.session.execute(select(Campaign).order_by(Campaign.created_at.desc()))
        return result.scalars().all()

    async def get_campaign(self, campaign_id: int) -> Campaign | None:
        result = await self.session.execute(select(Campaign).where(Campaign.id == campaign_id))
        return result.scalar_one_or_none()

    async def list_newsletter_subscribers(self) -> list[NewsletterSubscriber]:
        result = await self.session.execute(select(NewsletterSubscriber).order_by(NewsletterSubscriber.created_at.desc()))
        return result.scalars().all()

    async def list_redirects(self) -> list[RedirectRule]:
        result = await self.session.execute(select(RedirectRule).order_by(RedirectRule.source_path.asc()))
        return result.scalars().all()

    async def get_redirect(self, redirect_id: int) -> RedirectRule | None:
        result = await self.session.execute(select(RedirectRule).where(RedirectRule.id == redirect_id))
        return result.scalar_one_or_none()

    async def list_media_assets(self, page: int = 1, page_size: int = 50):
        return await self.paginate(select(MediaAsset).order_by(MediaAsset.created_at.desc()), page=page, page_size=page_size)

    async def get_media_asset(self, media_id: int) -> MediaAsset | None:
        result = await self.session.execute(select(MediaAsset).where(MediaAsset.id == media_id))
        return result.scalar_one_or_none()

    async def list_uploaded_customer_files(self, page: int = 1, page_size: int = 50):
        return await self.paginate(select(UploadedCustomerFile).order_by(UploadedCustomerFile.created_at.desc()), page=page, page_size=page_size)

    async def get_uploaded_customer_file(self, file_id: int) -> UploadedCustomerFile | None:
        result = await self.session.execute(select(UploadedCustomerFile).where(UploadedCustomerFile.id == file_id))
        return result.scalar_one_or_none()

    async def list_roles(self) -> list[Role]:
        result = await self.session.execute(select(Role).options(selectinload(Role.permissions)).order_by(Role.name.asc()))
        return result.scalars().all()

    async def list_shipping_methods(self) -> list[ShippingMethod]:
        result = await self.session.execute(select(ShippingMethod).order_by(ShippingMethod.name.asc()))
        return result.scalars().all()

    async def get_shipping_method(self, method_id: int) -> ShippingMethod | None:
        result = await self.session.execute(select(ShippingMethod).where(ShippingMethod.id == method_id))
        return result.scalar_one_or_none()

    async def list_shipping_rules(self) -> list[ShippingRateRule]:
        result = await self.session.execute(select(ShippingRateRule).order_by(ShippingRateRule.id.desc()))
        return result.scalars().all()

    async def get_shipping_rule(self, rule_id: int) -> ShippingRateRule | None:
        result = await self.session.execute(select(ShippingRateRule).where(ShippingRateRule.id == rule_id))
        return result.scalar_one_or_none()

    async def list_tax_rules(self) -> list[TaxRule]:
        result = await self.session.execute(select(TaxRule).order_by(TaxRule.id.desc()))
        return result.scalars().all()

    async def get_tax_rule(self, tax_rule_id: int) -> TaxRule | None:
        result = await self.session.execute(select(TaxRule).where(TaxRule.id == tax_rule_id))
        return result.scalar_one_or_none()

    async def create_activity_log(self, **data) -> AdminActivityLog:
        log = AdminActivityLog(**data)
        self.session.add(log)
        await self.session.flush()
        return log

    async def list_activity_logs(self, page: int = 1, page_size: int = 50):
        return await self.paginate(select(AdminActivityLog).order_by(AdminActivityLog.created_at.desc()), page=page, page_size=page_size)

    async def list_inventory_movements(self, page: int = 1, page_size: int = 50):
        return await self.paginate(select(InventoryMovement).order_by(InventoryMovement.created_at.desc()), page=page, page_size=page_size)

    async def list_coupons(self, page: int = 1, page_size: int = 20):
        return await self.paginate(select(Coupon).order_by(Coupon.created_at.desc()), page=page, page_size=page_size)

    async def list_reviews(self, page: int = 1, page_size: int = 50):
        return await self.paginate(select(ProductReview).order_by(ProductReview.created_at.desc()), page=page, page_size=page_size)
