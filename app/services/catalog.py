from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.catalog import (
    Category,
    CategoryMeta,
    Product,
    ProductCustomizationRule,
    ProductImage,
    ProductMeta,
    ProductRelation,
    ProductReview,
    ProductSpecification,
    ProductTag,
    ProductVariant,
)
from app.repositories.catalog import CatalogRepository
from app.schemas.catalog import CategoryWrite, CustomizationRuleWrite, ProductReviewCreate, ProductReviewModerationUpdate, ProductWrite
from app.services.customization_resolver import CustomizationResolver
from app.utils.text import slugify


class CatalogService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = CatalogRepository(session)

    async def list_categories(self) -> list[Category]:
        return await self.repository.list_categories()

    async def get_category(self, category_id: int) -> Category:
        category = await self.repository.get_category(category_id)
        if not category:
            raise AppException("Category not found", 404)
        return category

    async def create_category(self, payload: CategoryWrite) -> Category:
        category = Category(name=payload.name, parent_id=payload.parent_id)
        category.metadata_record = CategoryMeta(
            slug=payload.slug or slugify(payload.name),
            description=payload.description,
            image_url=payload.image_url,
            sort_order=payload.sort_order,
            is_enabled=payload.is_enabled,
            meta_title=payload.meta_title,
            meta_description=payload.meta_description,
        )
        await self.repository.save(category)
        await self.session.commit()
        return await self.get_category(category.id)

    async def update_category(self, category_id: int, payload: CategoryWrite) -> Category:
        category = await self.get_category(category_id)
        category.name = payload.name
        category.parent_id = payload.parent_id
        if category.metadata_record is None:
            category.metadata_record = CategoryMeta(slug=payload.slug or slugify(payload.name))
        category.metadata_record.slug = payload.slug or slugify(payload.name)
        category.metadata_record.description = payload.description
        category.metadata_record.image_url = payload.image_url
        category.metadata_record.sort_order = payload.sort_order
        category.metadata_record.is_enabled = payload.is_enabled
        category.metadata_record.meta_title = payload.meta_title
        category.metadata_record.meta_description = payload.meta_description
        await self.session.commit()
        return await self.get_category(category.id)

    async def delete_category(self, category_id: int) -> None:
        category = await self.get_category(category_id)
        await self.repository.delete(category)
        await self.session.commit()

    async def list_products(self, **filters):
        items, total = await self.repository.list_products(**filters)
        # Apply the virtual rules for each product in the list
        for item in items:
            item.customization_rules = await CustomizationResolver.resolve_rules(item, self.session)
        return items, total

    async def get_product(self, product_id: int | None = None, slug: str | None = None) -> Product:
        product = None
        if product_id is not None:
            product = await self.repository.get_product(product_id)
        elif slug is not None:
            product = await self.repository.get_product_by_slug(slug)
        if not product:
            raise AppException("Product not found", 404)
            
        # Apply the virtual rules on top of DB rules
        product.customization_rules = await CustomizationResolver.resolve_rules(product, self.session)
        return product

    async def create_product(self, payload: ProductWrite) -> Product:
        product = Product(
            wp_id=payload.wp_id,
            title=payload.title,
            content=payload.content,
            sku=payload.sku,
            price=payload.price,
            stock_quantity=payload.stock_quantity,
            stock_status=payload.stock_status,
            featured_image_url=payload.featured_image_url,
            category_id=payload.category_id,
        )
        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def update_product(self, product_id: int, payload: ProductWrite) -> Product:
        product = await self.get_product(product_id)
        product.wp_id = payload.wp_id
        product.title = payload.title
        product.content = payload.content
        product.sku = payload.sku
        product.price = payload.price
        product.stock_quantity = payload.stock_quantity
        product.stock_status = payload.stock_status
        product.featured_image_url = payload.featured_image_url
        product.category_id = payload.category_id
        await self._sync_product(product, payload)
        await self.session.commit()
        return await self.get_product(product.id)

    async def delete_product(self, product_id: int) -> None:
        product = await self.get_product(product_id)
        await self.repository.delete(product)
        await self.session.commit()

    async def bulk_import(self, products: list[ProductWrite]) -> list[Product]:
        created: list[Product] = []
        for payload in products:
            product = await self.create_product(payload)
            # Resolve rules for the new product
            product.customization_rules = await CustomizationResolver.resolve_rules(product, self.session)
            created.append(product)
        return created

    async def bulk_update_prices(self, items: list[dict]) -> list[Product]:
        updated: list[Product] = []
        for item in items:
            product = await self.get_product(item["product_id"])
            product.price = Decimal(str(item["price"]))
            updated.append(product)
        await self.session.commit()
        return updated

    async def bulk_delete(self, product_ids: list[int]) -> None:
        for product_id in product_ids:
            product = await self.get_product(product_id)
            await self.repository.delete(product)
        await self.session.commit()

    async def bulk_update_stock(self, items: list[dict]) -> list[Product]:
        updated: list[Product] = []
        for item in items:
            product = await self.get_product(item["product_id"])
            product.stock_quantity = int(item["stock_quantity"])
            if product.stock_quantity <= 0:
                product.stock_status = "out_of_stock"
            elif product.stock_quantity <= 5:
                product.stock_status = "low_stock"
            else:
                product.stock_status = "in_stock"
            updated.append(product)
        await self.session.commit()
        return updated

    async def add_review(self, product_id: int, user_id: int | None, payload: ProductReviewCreate):
        await self.get_product(product_id)
        review = ProductReview(
            product_id=product_id,
            user_id=user_id,
            rating=payload.rating,
            title=payload.title,
            body=payload.body,
            status="pending",
        )
        await self.repository.save(review)
        await self.session.commit()
        await self.session.refresh(review)
        return review

    async def list_reviews(self, **filters):
        return await self.repository.list_reviews(**filters)

    async def get_filters(
        self,
        search: str | None = None,
        category_id: int | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        size: str | None = None,
    ):
        from app.schemas.catalog import FilterOptions
        filter_data = await self.repository.get_filters(
            search=search,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            size=size,
        )
        return FilterOptions.model_validate(filter_data)

    async def moderate_review(self, review_id: int, payload: ProductReviewModerationUpdate) -> ProductReview:
        review = await self.repository.get_review(review_id)
        if not review:
            raise AppException("Review not found", 404)
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(review, field, value)
        await self.session.commit()
        await self.session.refresh(review)
        return review

    async def add_customization_rule(self, product_id: int, payload: CustomizationRuleWrite) -> ProductCustomizationRule:
        await self.get_product(product_id)
        rule = ProductCustomizationRule(product_id=product_id, **payload.model_dump())
        self.session.add(rule)
        await self.session.commit()
        await self.session.refresh(rule)
        return rule

    async def update_customization_rule(self, rule_id: int, payload: CustomizationRuleWrite) -> ProductCustomizationRule:
        from sqlalchemy import select
        result = await self.session.execute(select(ProductCustomizationRule).where(ProductCustomizationRule.id == rule_id))
        rule = result.scalar_one_or_none()
        if not rule:
            raise AppException("Customization rule not found", 404)
        
        for key, value in payload.model_dump().items():
            setattr(rule, key, value)
        
        await self.session.commit()
        await self.session.refresh(rule)
        return rule

    async def remove_customization_rule(self, rule_id: int) -> None:
        from sqlalchemy import select
        result = await self.session.execute(select(ProductCustomizationRule).where(ProductCustomizationRule.id == rule_id))
        rule = result.scalar_one_or_none()
        if not rule:
            raise AppException("Customization rule not found", 404)
        
        await self.session.delete(rule)
        await self.session.commit()

    async def sync_metadata(self) -> dict:
        # Sync Products
        from sqlalchemy import select
        from app.models.catalog import Product, ProductMeta, Category, CategoryMeta
        
        # Products
        stmt = select(Product).outerjoin(ProductMeta).where(ProductMeta.product_id == None)
        result = await self.session.execute(stmt)
        products_missing = result.scalars().all()
        
        synced_products = 0
        for product in products_missing:
            base_slug = slugify(product.title)
            slug = base_slug
            counter = 1
            # Simple collision check
            while await self.repository.get_product_by_slug(slug):
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            product.metadata_record = ProductMeta(
                slug=slug,
                is_enabled=True,
                is_featured=False
            )
            synced_products += 1
        
        # Categories
        stmt = select(Category).outerjoin(CategoryMeta).where(CategoryMeta.category_id == None)
        result = await self.session.execute(stmt)
        categories_missing = result.scalars().all()
        
        synced_categories = 0
        for category in categories_missing:
            base_slug = slugify(category.name)
            slug = base_slug
            counter = 1
            while await self.repository.get_category_by_slug(slug):
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            category.metadata_record = CategoryMeta(
                slug=slug,
                is_enabled=True
            )
            synced_categories += 1
            
        await self.session.commit()
        return {
            "synced_products": synced_products,
            "synced_categories": synced_categories
        }

    async def _sync_product(self, product: Product, payload: ProductWrite) -> None:
        # Create metadata if it doesn't exist
        if product.metadata_record is None:
            product.metadata_record = ProductMeta(
                product_id=product.id,
                slug=slugify(product.title),
                sort_order=0,
                popularity_score=0,
                low_stock_threshold=5
            )
            self.session.add(product.metadata_record)
        
        # Only update if meta is provided
        if payload.meta:
            meta = payload.meta
            product.metadata_record.slug = meta.slug or slugify(product.title)
            product.metadata_record.short_description = meta.short_description
            product.metadata_record.is_enabled = meta.is_enabled
            product.metadata_record.is_featured = meta.is_featured
            product.metadata_record.meta_title = meta.meta_title
            product.metadata_record.meta_description = meta.meta_description
            product.metadata_record.sort_order = meta.sort_order
            product.metadata_record.popularity_score = meta.popularity_score
            product.metadata_record.low_stock_threshold = meta.low_stock_threshold
            product.metadata_record.size_guide = meta.size_guide
