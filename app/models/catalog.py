from datetime import datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy import Boolean, CheckConstraint, Column, DECIMAL, ForeignKey, Integer, String, Table, Text, TIMESTAMP, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

product_tag_link = Table(
    "product_tag_link",
    Base.metadata,
    Column("product_id", ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("product_tags.id", ondelete="CASCADE"), primary_key=True),
)

product_category_link = Table(
    "product_categories",
    Base.metadata,
    Column("product_id", ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)

class Settings(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    value: Mapped[str] = mapped_column(String, nullable=False)

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)

    parent: Mapped["Category | None"] = relationship(remote_side=[id], back_populates="children")
    children: Mapped[list["Category"]] = relationship(back_populates="parent")
    metadata_record: Mapped["CategoryMeta | None"] = relationship(back_populates="category", uselist=False)
    primary_products: Mapped[list["Product"]] = relationship(back_populates="primary_category")
    products: Mapped[list["Product"]] = relationship(secondary=product_category_link, back_populates="categories")
    customization_rules: Mapped[list["CategoryCustomizationRule"]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )


class CategoryMeta(Base, TimestampMixin):
    __tablename__ = "category_meta"

    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    meta_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    category: Mapped["Category"] = relationship(back_populates="metadata_record")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    wp_id: Mapped[int | None] = mapped_column(Integer, unique=True, nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    price: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), default=Decimal("0.00"), nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stock_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    featured_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=sa.text("now()"), default=datetime.now)

    primary_category: Mapped["Category | None"] = relationship(back_populates="primary_products")
    categories: Mapped[list["Category"]] = relationship(secondary=product_category_link, back_populates="products")
    metadata_record: Mapped["ProductMeta | None"] = relationship(back_populates="product", uselist=False)
    images: Mapped[list["ProductImage"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    variants: Mapped[list["ProductVariant"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    specs: Mapped[list["ProductSpecification"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    tags: Mapped[list["ProductTag"]] = relationship(secondary=product_tag_link, back_populates="products")
    customization_rules: Mapped[list["ProductCustomizationRule"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    related_products: Mapped[list["ProductRelation"]] = relationship(
        foreign_keys="ProductRelation.product_id", back_populates="product", cascade="all, delete-orphan"
    )
    reviews: Mapped[list["ProductReview"]] = relationship(back_populates="product", cascade="all, delete-orphan")


class ProductMeta(Base, TimestampMixin):
    __tablename__ = "product_meta"

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    short_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    meta_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    popularity_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    size_guide: Mapped[str | None] = mapped_column(Text, nullable=True)

    product: Mapped["Product"] = relationship(back_populates="metadata_record")


class ProductImage(Base, TimestampMixin):
    __tablename__ = "product_images"
    __table_args__ = (UniqueConstraint("product_id", "sort_order", name="uq_product_images_product_order"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    image_url: Mapped[str] = mapped_column(Text)
    alt_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    product: Mapped["Product"] = relationship(back_populates="images")


class ProductVariant(Base, TimestampMixin):
    __tablename__ = "product_variants"
    __table_args__ = (UniqueConstraint("product_id", "sku", name="uq_product_variants_product_sku"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(150))
    option_values: Mapped[dict] = mapped_column(JSONB)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    price_override: Mapped[Decimal | None] = mapped_column(DECIMAL(12, 2), nullable=True)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    product: Mapped["Product"] = relationship(back_populates="variants")


class ProductSpecification(Base, TimestampMixin):
    __tablename__ = "product_specifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(150))
    value: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    product: Mapped["Product"] = relationship(back_populates="specs")


class ProductTag(Base):
    __tablename__ = "product_tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True)

    products: Mapped[list["Product"]] = relationship(secondary=product_tag_link, back_populates="tags")


class ProductCustomizationRule(Base, TimestampMixin):
    __tablename__ = "product_customization_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    field_type: Mapped[str] = mapped_column(String(50))
    label: Mapped[str] = mapped_column(String(150))
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_file_size_mb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    allowed_file_types: Mapped[str | None] = mapped_column(Text, nullable=True)
    help_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_rules: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    product: Mapped["Product"] = relationship(back_populates="customization_rules")


class CategoryCustomizationRule(Base, TimestampMixin):
    __tablename__ = "category_customization_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), index=True)
    field_type: Mapped[str] = mapped_column(String(50))
    label: Mapped[str] = mapped_column(String(100))
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    max_file_size_mb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    allowed_file_types: Mapped[str | None] = mapped_column(String(255), nullable=True)
    help_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_rules: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    category: Mapped["Category"] = relationship(back_populates="customization_rules")


class ProductRelation(Base):
    __tablename__ = "product_relations"
    __table_args__ = (UniqueConstraint("product_id", "related_product_id", name="uq_product_relations_pair"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    related_product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    relation_type: Mapped[str] = mapped_column(String(50), default="related")

    product: Mapped["Product"] = relationship(foreign_keys=[product_id], back_populates="related_products")


class ProductReview(Base, TimestampMixin):
    __tablename__ = "product_reviews"
    __table_args__ = (CheckConstraint("rating >= 1 AND rating <= 5", name="ck_product_reviews_rating"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    rating: Mapped[int] = mapped_column(Integer)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    admin_reply: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_spam: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    product: Mapped["Product"] = relationship(back_populates="reviews")
