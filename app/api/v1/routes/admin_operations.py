from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_roles
from app.models.user import User
from app.schemas.admin import (
    BannerRead,
    BannerWrite,
    CampaignRead,
    CampaignWrite,
    CouponRead,
    CouponWrite,
    InventoryAdjustmentWrite,
    InventoryMovementRead,
    RedirectRuleRead,
    RedirectRuleWrite,
    ShippingMethodRead,
    ShippingMethodWrite,
    ShippingRateRuleRead,
    ShippingRateRuleWrite,
    StoreSettingRead,
    StoreSettingWrite,
    TaxRuleRead,
    TaxRuleWrite,
)
from app.schemas.common import ActionResponse, PaginatedResponse
from app.schemas.media import MediaAssetRead
from app.schemas.settings import NewsletterSubscriberRead
from app.services.admin import AdminService
from app.services.catalog import CatalogService
from app.services.media import MediaService

router = APIRouter(dependencies=[Depends(require_roles("super_admin", "admin", "manager"))])


@router.get("/coupons", response_model=PaginatedResponse)
async def list_coupons(page: int = 1, page_size: int = 20, session: AsyncSession = Depends(get_db)):
    service = AdminService(session)
    items, total = await service.list_coupons(page=page, page_size=page_size)
    return PaginatedResponse(items=[CouponRead.model_validate(item) for item in items], total=total, page=page, page_size=page_size)


@router.post("/coupons", response_model=CouponRead)
async def create_coupon(payload: CouponWrite, session: AsyncSession = Depends(get_db)) -> CouponRead:
    service = AdminService(session)
    coupon = await service.create_coupon(payload)
    return CouponRead.model_validate(coupon)


@router.put("/coupons/{coupon_id}", response_model=CouponRead)
async def update_coupon(coupon_id: int, payload: CouponWrite, session: AsyncSession = Depends(get_db)) -> CouponRead:
    service = AdminService(session)
    coupon = await service.update_coupon(coupon_id, payload)
    return CouponRead.model_validate(coupon)


@router.delete("/coupons/{coupon_id}", response_model=ActionResponse)
async def delete_coupon(coupon_id: int, session: AsyncSession = Depends(get_db)) -> ActionResponse:
    service = AdminService(session)
    await service.delete_coupon(coupon_id)
    return ActionResponse(message="Coupon deleted")


@router.get("/inventory/movements", response_model=PaginatedResponse)
async def inventory_movements(page: int = 1, page_size: int = 50, session: AsyncSession = Depends(get_db)):
    service = AdminService(session)
    items, total = await service.list_inventory_movements(page=page, page_size=page_size)
    return PaginatedResponse(items=[InventoryMovementRead.model_validate(item) for item in items], total=total, page=page, page_size=page_size)


@router.post("/inventory/adjustments", response_model=InventoryMovementRead)
async def adjust_inventory(
    payload: InventoryAdjustmentWrite,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> InventoryMovementRead:
    service = AdminService(session)
    movement = await service.adjust_inventory(payload, admin_user_id=current_user.id)
    return InventoryMovementRead.model_validate(movement)


@router.get("/shipping-methods", response_model=list[ShippingMethodRead])
async def shipping_methods(session: AsyncSession = Depends(get_db)) -> list[ShippingMethodRead]:
    service = AdminService(session)
    methods = await service.list_shipping_methods()
    return [ShippingMethodRead.model_validate(item) for item in methods]


@router.post("/shipping-methods", response_model=ShippingMethodRead)
async def create_shipping_method(payload: ShippingMethodWrite, session: AsyncSession = Depends(get_db)) -> ShippingMethodRead:
    service = AdminService(session)
    method = await service.create_shipping_method(payload)
    return ShippingMethodRead.model_validate(method)


@router.put("/shipping-methods/{method_id}", response_model=ShippingMethodRead)
async def update_shipping_method(method_id: int, payload: ShippingMethodWrite, session: AsyncSession = Depends(get_db)) -> ShippingMethodRead:
    service = AdminService(session)
    method = await service.update_shipping_method(method_id, payload)
    return ShippingMethodRead.model_validate(method)


@router.delete("/shipping-methods/{method_id}", response_model=ActionResponse)
async def delete_shipping_method(method_id: int, session: AsyncSession = Depends(get_db)) -> ActionResponse:
    service = AdminService(session)
    await service.delete_shipping_method(method_id)
    return ActionResponse(message="Shipping method deleted")


@router.get("/shipping-rules", response_model=list[ShippingRateRuleRead])
async def shipping_rules(session: AsyncSession = Depends(get_db)) -> list[ShippingRateRuleRead]:
    service = AdminService(session)
    rules = await service.list_shipping_rules()
    return [ShippingRateRuleRead.model_validate(item) for item in rules]


@router.post("/shipping-rules", response_model=ShippingRateRuleRead)
async def create_shipping_rule(payload: ShippingRateRuleWrite, session: AsyncSession = Depends(get_db)) -> ShippingRateRuleRead:
    service = AdminService(session)
    rule = await service.create_shipping_rule(payload)
    return ShippingRateRuleRead.model_validate(rule)


@router.put("/shipping-rules/{rule_id}", response_model=ShippingRateRuleRead)
async def update_shipping_rule(rule_id: int, payload: ShippingRateRuleWrite, session: AsyncSession = Depends(get_db)) -> ShippingRateRuleRead:
    service = AdminService(session)
    rule = await service.update_shipping_rule(rule_id, payload)
    return ShippingRateRuleRead.model_validate(rule)


@router.delete("/shipping-rules/{rule_id}", response_model=ActionResponse)
async def delete_shipping_rule(rule_id: int, session: AsyncSession = Depends(get_db)) -> ActionResponse:
    service = AdminService(session)
    await service.delete_shipping_rule(rule_id)
    return ActionResponse(message="Shipping rule deleted")


@router.get("/tax-rules", response_model=list[TaxRuleRead])
async def tax_rules(session: AsyncSession = Depends(get_db)) -> list[TaxRuleRead]:
    service = AdminService(session)
    rules = await service.list_tax_rules()
    return [TaxRuleRead.model_validate(item) for item in rules]


@router.post("/tax-rules", response_model=TaxRuleRead)
async def create_tax_rule(payload: TaxRuleWrite, session: AsyncSession = Depends(get_db)) -> TaxRuleRead:
    service = AdminService(session)
    rule = await service.create_tax_rule(payload)
    return TaxRuleRead.model_validate(rule)


@router.put("/tax-rules/{tax_rule_id}", response_model=TaxRuleRead)
async def update_tax_rule(tax_rule_id: int, payload: TaxRuleWrite, session: AsyncSession = Depends(get_db)) -> TaxRuleRead:
    service = AdminService(session)
    rule = await service.update_tax_rule(tax_rule_id, payload)
    return TaxRuleRead.model_validate(rule)


@router.delete("/tax-rules/{tax_rule_id}", response_model=ActionResponse)
async def delete_tax_rule(tax_rule_id: int, session: AsyncSession = Depends(get_db)) -> ActionResponse:
    service = AdminService(session)
    await service.delete_tax_rule(tax_rule_id)
    return ActionResponse(message="Tax rule deleted")


@router.get("/media", response_model=PaginatedResponse)
async def media_assets(page: int = 1, page_size: int = 50, session: AsyncSession = Depends(get_db)):
    service = MediaService(session)
    items, total = await service.list_media_assets(page=page, page_size=page_size)
    return PaginatedResponse(items=[MediaAssetRead.model_validate(item) for item in items], total=total, page=page, page_size=page_size)


@router.post("/media/upload", response_model=MediaAssetRead)
async def upload_media(
    file: UploadFile = File(...),
    product_id: int | None = Form(default=None),
    category_id: int | None = Form(default=None),
    alt_text: str | None = Form(default=None),
    is_public: bool = Form(default=True),
    session: AsyncSession = Depends(get_db),
) -> MediaAssetRead:
    service = MediaService(session)
    asset = await service.upload_media_asset(file, product_id=product_id, category_id=category_id, alt_text=alt_text, is_public=is_public)
    return MediaAssetRead.model_validate(asset)


@router.delete("/media/{media_id}", response_model=ActionResponse)
async def delete_media(media_id: int, session: AsyncSession = Depends(get_db)) -> ActionResponse:
    service = MediaService(session)
    await service.delete_media_asset(media_id)
    return ActionResponse(message="Media asset deleted")


@router.post("/media/{media_id}/compress", response_model=ActionResponse)
async def compress_media(media_id: int, session: AsyncSession = Depends(get_db)) -> ActionResponse:
    service = MediaService(session)
    result = await service.compress_media_asset(media_id)
    return ActionResponse(message=result["message"])


@router.get("/settings", response_model=list[StoreSettingRead])
async def list_settings(session: AsyncSession = Depends(get_db)) -> list[StoreSettingRead]:
    service = AdminService(session)
    settings_items = await service.list_settings()
    return [StoreSettingRead.model_validate(item) for item in settings_items]


@router.put("/settings", response_model=StoreSettingRead)
async def upsert_setting(payload: StoreSettingWrite, session: AsyncSession = Depends(get_db)) -> StoreSettingRead:
    service = AdminService(session)
    setting = await service.upsert_setting(payload)
    return StoreSettingRead.model_validate(setting)


@router.get("/marketing/banners", response_model=list[BannerRead])
async def list_banners(session: AsyncSession = Depends(get_db)) -> list[BannerRead]:
    service = AdminService(session)
    banners = await service.list_banners()
    return [BannerRead.model_validate(item) for item in banners]


@router.post("/marketing/banners", response_model=BannerRead)
async def create_banner(payload: BannerWrite, session: AsyncSession = Depends(get_db)) -> BannerRead:
    service = AdminService(session)
    banner = await service.create_banner(payload)
    return BannerRead.model_validate(banner)


@router.put("/marketing/banners/{banner_id}", response_model=BannerRead)
async def update_banner(banner_id: int, payload: BannerWrite, session: AsyncSession = Depends(get_db)) -> BannerRead:
    service = AdminService(session)
    banner = await service.update_banner(banner_id, payload)
    return BannerRead.model_validate(banner)


@router.delete("/marketing/banners/{banner_id}", response_model=ActionResponse)
async def delete_banner(banner_id: int, session: AsyncSession = Depends(get_db)) -> ActionResponse:
    service = AdminService(session)
    await service.delete_banner(banner_id)
    return ActionResponse(message="Banner deleted")


@router.get("/marketing/campaigns", response_model=list[CampaignRead])
async def list_campaigns(session: AsyncSession = Depends(get_db)) -> list[CampaignRead]:
    service = AdminService(session)
    campaigns = await service.list_campaigns()
    return [CampaignRead.model_validate(item) for item in campaigns]


@router.post("/marketing/campaigns", response_model=CampaignRead)
async def create_campaign(payload: CampaignWrite, session: AsyncSession = Depends(get_db)) -> CampaignRead:
    service = AdminService(session)
    campaign = await service.create_campaign(payload)
    return CampaignRead.model_validate(campaign)


@router.put("/marketing/campaigns/{campaign_id}", response_model=CampaignRead)
async def update_campaign(campaign_id: int, payload: CampaignWrite, session: AsyncSession = Depends(get_db)) -> CampaignRead:
    service = AdminService(session)
    campaign = await service.update_campaign(campaign_id, payload)
    return CampaignRead.model_validate(campaign)


@router.delete("/marketing/campaigns/{campaign_id}", response_model=ActionResponse)
async def delete_campaign(campaign_id: int, session: AsyncSession = Depends(get_db)) -> ActionResponse:
    service = AdminService(session)
    await service.delete_campaign(campaign_id)
    return ActionResponse(message="Campaign deleted")


@router.post("/marketing/campaigns/{campaign_id}/dispatch")
async def dispatch_campaign(campaign_id: int, session: AsyncSession = Depends(get_db)):
    service = AdminService(session)
    return await service.dispatch_campaign(campaign_id)


@router.get("/marketing/newsletter", response_model=list[NewsletterSubscriberRead])
async def newsletter_subscribers(session: AsyncSession = Depends(get_db)) -> list[NewsletterSubscriberRead]:
    service = AdminService(session)
    subscribers = await service.repository.list_newsletter_subscribers()
    return [NewsletterSubscriberRead.model_validate(item) for item in subscribers]


@router.post("/marketing/newsletter/subscribe", response_model=NewsletterSubscriberRead)
async def subscribe_newsletter(email: str, session: AsyncSession = Depends(get_db)) -> NewsletterSubscriberRead:
    service = AdminService(session)
    subscriber = await service.subscribe_newsletter(email)
    return NewsletterSubscriberRead.model_validate(subscriber)


@router.get("/seo/redirects", response_model=list[RedirectRuleRead])
async def list_redirects(session: AsyncSession = Depends(get_db)) -> list[RedirectRuleRead]:
    service = AdminService(session)
    redirects = await service.list_redirects()
    return [RedirectRuleRead.model_validate(item) for item in redirects]


@router.post("/seo/redirects", response_model=RedirectRuleRead)
async def create_redirect(payload: RedirectRuleWrite, session: AsyncSession = Depends(get_db)) -> RedirectRuleRead:
    service = AdminService(session)
    redirect = await service.create_redirect(payload)
    return RedirectRuleRead.model_validate(redirect)


@router.put("/seo/redirects/{redirect_id}", response_model=RedirectRuleRead)
async def update_redirect(redirect_id: int, payload: RedirectRuleWrite, session: AsyncSession = Depends(get_db)) -> RedirectRuleRead:
    service = AdminService(session)
    redirect = await service.update_redirect(redirect_id, payload)
    return RedirectRuleRead.model_validate(redirect)


@router.delete("/seo/redirects/{redirect_id}", response_model=ActionResponse)
async def delete_redirect(redirect_id: int, session: AsyncSession = Depends(get_db)) -> ActionResponse:
    service = AdminService(session)
    await service.delete_redirect(redirect_id)
    return ActionResponse(message="Redirect deleted")


@router.get("/seo/sitemap")
async def sitemap(session: AsyncSession = Depends(get_db)):
    service = CatalogService(session)
    products, _ = await service.list_products(page=1, page_size=1000)
    categories = await service.list_categories()
    return {
        "products": [product.metadata_record.slug for product in products if product.metadata_record],
        "categories": [category["metadata_record"].slug if isinstance(category, dict) and category["metadata_record"] else (category.metadata_record.slug if hasattr(category, "metadata_record") and category.metadata_record else None) for category in categories],
    }
