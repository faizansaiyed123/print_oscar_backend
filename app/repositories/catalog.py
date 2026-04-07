from decimal import Decimal

from sqlalchemy import Text, asc, cast, desc, distinct, func, or_, select, union_all
from sqlalchemy.orm import selectinload

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
    product_category_link,
)
from app.repositories.base import BaseRepository


class CatalogRepository(BaseRepository):
    async def list_categories(self):
        result = await self.session.execute(
            select(Category)
            .options(selectinload(Category.metadata_record))
            .order_by(Category.name.asc())
        )

        categories = result.scalars().unique().all()

        # ✅ Convert to plain dict (prevents MissingGreenlet)
        category_map = {
            c.id: {
                "id": c.id,
                "name": c.name,
                "parent_id": c.parent_id,
                "metadata_record": c.metadata_record,
                "children": [],
            }
            for c in categories
        }

        # ✅ Build tree manually
        for c in category_map.values():
            if c["parent_id"] and c["parent_id"] in category_map:
                category_map[c["parent_id"]]["children"].append(c)

        # ✅ Return only root categories
        return [c for c in category_map.values() if c["parent_id"] is None]

    async def get_category(self, category_id: int):
        result = await self.session.execute(
            select(Category)
            .options(selectinload(Category.metadata_record))
            .where(Category.id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_category_by_slug(self, slug: str):
        result = await self.session.execute(
            select(Category)
            .join(CategoryMeta, CategoryMeta.category_id == Category.id)
            .options(selectinload(Category.metadata_record))
            .where(CategoryMeta.slug == slug)
        )
        return result.scalar_one_or_none()

    async def list_products(
        self,
        *,
        search: str | None = None,
        category_id: int | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        size: str | None = None,
        sort_by: str = "newest",
        page: int = 1,
        page_size: int = 20,
    ):
        statement = (
            select(Product)
            .outerjoin(ProductMeta, ProductMeta.product_id == Product.id)
            .options(
                selectinload(Product.metadata_record),
                selectinload(Product.images),
                selectinload(Product.variants),
                selectinload(Product.specs),
                selectinload(Product.primary_category),
                selectinload(Product.categories).selectinload(Category.metadata_record),
                selectinload(Product.customization_rules),
                selectinload(Product.reviews),
            )
        )

        if search:
            pattern = f"%{search}%"
            statement = statement.where(
                or_(
                    Product.title.ilike(pattern),
                    Product.content.ilike(pattern),
                    Product.sku.ilike(pattern),
                )
            )

        if category_id:
            statement = statement.where(
                or_(
                    Product.category_id == category_id,
                    Product.categories.any(Category.id == category_id),
                )
            )

        if min_price is not None:
            statement = statement.where(Product.price >= min_price)

        if max_price is not None:
            statement = statement.where(Product.price <= max_price)

        if size:
            statement = statement.where(
                Product.variants.any(
                    ProductVariant.option_values["size"].astext == size
                )
            )

        ordering = {
            "price_asc": asc(Product.price),
            "price_desc": desc(Product.price),
            "popularity": desc(func.coalesce(ProductMeta.popularity_score, 0)),
            "newest": desc(Product.created_at),
        }.get(sort_by, desc(Product.created_at))

        statement = statement.order_by(ordering, Product.id.desc())

        return await self.paginate(statement, page=page, page_size=page_size)

    async def get_product(self, product_id: int):
        statement = (
            select(Product)
            .options(
                selectinload(Product.metadata_record),
                selectinload(Product.images),
                selectinload(Product.variants),
                selectinload(Product.specs),
                selectinload(Product.tags),
                selectinload(Product.primary_category),
                selectinload(Product.categories).selectinload(Category.metadata_record),
                selectinload(Product.customization_rules),
                selectinload(Product.reviews),
                selectinload(Product.related_products),
            )
            .where(Product.id == product_id)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_product_by_slug(self, slug: str):
        statement = (
            select(Product)
            .join(ProductMeta, ProductMeta.product_id == Product.id)
            .options(
                selectinload(Product.metadata_record),
                selectinload(Product.images),
                selectinload(Product.variants),
                selectinload(Product.specs),
                selectinload(Product.tags),
                selectinload(Product.primary_category),
                selectinload(Product.categories).selectinload(Category.metadata_record),
                selectinload(Product.customization_rules),
                selectinload(Product.reviews),
                selectinload(Product.related_products),
            )
            .where(ProductMeta.slug == slug)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_reviews(
        self,
        *,
        product_id: int | None = None,
        user_id: int | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ):
        statement = select(ProductReview).order_by(
            ProductReview.created_at.desc()
        )

        if product_id:
            statement = statement.where(ProductReview.product_id == product_id)

        if user_id:
            statement = statement.where(ProductReview.user_id == user_id)

        if status:
            statement = statement.where(ProductReview.status == status)

        return await self.paginate(statement, page=page, page_size=page_size)

    async def get_review(self, review_id: int):
        result = await self.session.execute(
            select(ProductReview).where(ProductReview.id == review_id)
        )
        return result.scalar_one_or_none()

    async def get_tag_by_name(self, name: str):
        result = await self.session.execute(
            select(ProductTag).where(
                func.lower(ProductTag.name) == name.lower()
            )
        )
        return result.scalar_one_or_none()

    async def get_related_products(self, product_ids: list[int]):
        if not product_ids:
            return []
        result = await self.session.execute(
            select(Product).where(Product.id.in_(product_ids))
        )
        return result.scalars().all()

    async def get_filters(
        self,
        search: str | None = None,
        category_id: int | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        size: str | None = None,
    ) -> dict:
        from app.models.catalog import Category, Product, ProductMeta, ProductVariant
        from sqlalchemy import func, distinct, text
        
        # Base filtered products query (matches list_products filters)
        product_stmt = select(Product.id).outerjoin(
            ProductMeta, ProductMeta.product_id == Product.id
        ).where(
            or_(
                ProductMeta.product_id == None,
                ProductMeta.is_enabled == True
            )
        )
        
        if search:
            pattern = f"%{search}%"
            product_stmt = product_stmt.where(
                or_(
                    Product.title.ilike(pattern),
                    Product.content.ilike(pattern),
                    Product.sku.ilike(pattern),
                )
            )
        
        if category_id:
            product_stmt = product_stmt.where(
                or_(
                    Product.category_id == category_id,
                    Product.categories.any(Category.id == category_id),
                )
            )
        
        if min_price is not None:
            product_stmt = product_stmt.where(Product.price >= min_price)
        if max_price is not None:
            product_stmt = product_stmt.where(Product.price <= max_price)
        
        if size:
            product_stmt = product_stmt.where(
                Product.variants.any(
                    ProductVariant.option_values["size"].astext == size,
                    ProductVariant.stock_quantity > 0,
                    ProductVariant.is_enabled == True
                )
            )
        
        filtered_products = product_stmt.subquery()
        
        # Price range
        price_result = await self.session.execute(
            select(
                func.coalesce(func.min(Product.price), 0).label('min_price'),
                func.coalesce(func.max(Product.price), 0).label('max_price')
            )
            .select_from(Product)
            .join(filtered_products, Product.id == filtered_products.c.id)
        )
        price_row = price_result.fetchone()
        price_range = {'min': price_row.min_price or 0, 'max': price_row.max_price or 0}
        
        # Categories with counts (include both primary and secondary)
        
        # Primary categories
        cat_primary = (
            select(Product.category_id.label('cat_id'), func.count(Product.id).label('count'))
            .join(filtered_products, Product.id == filtered_products.c.id)
            .where(Product.category_id != None)
            .group_by(Product.category_id)
        )
        
        # Secondary categories
        cat_secondary = (
            select(product_category_link.c.category_id.label('cat_id'), func.count(product_category_link.c.product_id).label('count'))
            .join(filtered_products, product_category_link.c.product_id == filtered_products.c.id)
            .group_by(product_category_link.c.category_id)
        )
        
        all_counts = union_all(cat_primary, cat_secondary).subquery()
        cat_counts = select(all_counts.c.cat_id, func.sum(all_counts.c.count).label('total_count')).group_by(all_counts.c.cat_id).subquery()
        
        cat_final_stmt = (
            select(Category.id, Category.name, cat_counts.c.total_count)
            .join(cat_counts, Category.id == cat_counts.c.cat_id)
            .order_by(cat_counts.c.total_count.desc())
        )
        
        cat_result = await self.session.execute(cat_final_stmt)
        categories = [
            {'id': row.id, 'name': row.name, 'count': row.total_count}
            for row in cat_result
        ]
        
        # Sizes: distinct from enabled/in-stock variants
        size_stmt = (
            select(
                distinct(ProductVariant.option_values["size"].astext).label("size")
            )
            .select_from(Product)
            .join(filtered_products, Product.id == filtered_products.c.id)
            .join(ProductVariant, Product.id == ProductVariant.product_id)
            .where(
                ProductVariant.stock_quantity > 0,
                ProductVariant.is_enabled == True,
                ProductVariant.option_values.has_key("size")
            )
            .order_by("size")
        )
        size_result = await self.session.execute(size_stmt)
        sizes = [row.size for row in size_result if row.size]
        
        # Colors: similar extraction
        color_stmt = (
            select(
                distinct(ProductVariant.option_values["color"].astext).label("color")
            )
            .select_from(Product)
            .join(filtered_products, Product.id == filtered_products.c.id)
            .join(ProductVariant, Product.id == ProductVariant.product_id)
            .where(
                ProductVariant.stock_quantity > 0,
                ProductVariant.is_enabled == True,
                ProductVariant.option_values.has_key("color")
            )
            .order_by("color")
        )
        color_result = await self.session.execute(color_stmt)
        colors = [row.color for row in color_result if row.color]
        
        return {
            'price_range': price_range,
            'categories': categories,
            'sizes': sizes,
            'colors': colors,
        }
