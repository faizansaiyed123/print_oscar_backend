from decimal import Decimal

from pydantic import BaseModel,Field

from app.schemas.common import ORMModel, TimestampedSchema


class CategoryMetaRead(TimestampedSchema):
    slug: str
    description: str | None = None
    image_url: str | None = None
    sort_order: int
    is_enabled: bool
    meta_title: str | None = None
    meta_description: str | None = None


class CategoryRead(ORMModel):
    id: int
    name: str
    parent_id: int | None = None
    count: int | None = None
    metadata_record: CategoryMetaRead | None = None


class CategoryTreeRead(CategoryRead):
    children: list["CategoryTreeRead"] = Field(default_factory=list)


class CategoryWrite(BaseModel):
    name: str
    parent_id: int | None = None
    slug: str | None = None
    description: str | None = None
    image_url: str | None = None
    sort_order: int = 0
    is_enabled: bool = True
    meta_title: str | None = None
    meta_description: str | None = None


class ProductImageRead(TimestampedSchema):
    id: int
    image_url: str
    alt_text: str | None = None
    sort_order: int
    is_featured: bool


class ProductImageWrite(BaseModel):
    image_url: str
    alt_text: str | None = None
    sort_order: int = 0
    is_featured: bool = False


class ProductVariantRead(TimestampedSchema):
    id: int
    name: str
    option_values: dict
    sku: str | None = None
    price_override: Decimal | None = None
    stock_quantity: int
    is_enabled: bool


class ProductVariantWrite(BaseModel):
    name: str
    option_values: dict
    sku: str | None = None
    price_override: Decimal | None = None
    stock_quantity: int = 0
    is_enabled: bool = True


class ProductSpecificationRead(TimestampedSchema):
    id: int
    name: str
    value: str
    sort_order: int


class ProductSpecificationWrite(BaseModel):
    name: str
    value: str
    sort_order: int = 0


class CustomizationRuleRead(TimestampedSchema):
    id: int
    field_type: str
    label: str
    is_required: bool
    max_file_size_mb: int | None = None
    allowed_file_types: str | None = None
    help_text: str | None = None
    validation_rules: dict | None = None
    is_enabled: bool


class CustomizationRuleWrite(BaseModel):
    field_type: str
    label: str
    is_required: bool = False
    max_file_size_mb: int | None = None
    allowed_file_types: str | None = None
    help_text: str | None = None
    validation_rules: dict | None = None
    is_enabled: bool = True


class ProductMetaRead(TimestampedSchema):
    slug: str
    short_description: str | None = None
    is_enabled: bool
    is_featured: bool
    meta_title: str | None = None
    meta_description: str | None = None
    sort_order: int
    popularity_score: int
    low_stock_threshold: int
    size_guide: str | None = None


class ProductMetaWrite(BaseModel):
    slug: str | None = None
    short_description: str | None = None
    is_enabled: bool = True
    is_featured: bool = False
    meta_title: str | None = None
    meta_description: str | None = None
    sort_order: int = 0
    popularity_score: int = 0
    low_stock_threshold: int = 5
    size_guide: str | None = None


class ProductReviewRead(TimestampedSchema):
    id: int
    user_id: int | None = None
    rating: int
    title: str | None = None
    body: str | None = None
    status: str
    admin_reply: str | None = None
    is_spam: bool


class ProductRead(ORMModel):
    id: int
    wp_id: int | None = None
    title: str
    content: str | None = None
    sku: str | None = None
    price: Decimal
    stock_quantity: int
    stock_status: str | None = None
    featured_image_url: str | None = None
    category_id: int | None = None
    metadata_record: ProductMetaRead | None = None
    categories: list[CategoryRead] = []
    images: list[ProductImageRead] = []
    variants: list[ProductVariantRead] = []
    specs: list[ProductSpecificationRead] = []
    customization_rules: list[CustomizationRuleRead] = []
    reviews: list[ProductReviewRead] = []


class ProductCardRead(ORMModel):
    id: int
    title: str
    price: Decimal
    stock_quantity: int
    stock_status: str | None = None
    featured_image_url: str | None = None
    category_id: int | None = None
    metadata_record: ProductMetaRead | None = None


class ProductWrite(BaseModel):
    wp_id: int | None = None
    title: str
    content: str | None = None
    sku: str | None = None
    price: Decimal
    stock_quantity: int = 0
    stock_status: str | None = None
    featured_image_url: str | None = None
    category_id: int | None = None
    category_ids: list[int] = []
    meta: ProductMetaWrite | None = None
    images: list[ProductImageWrite] = []
    variants: list[ProductVariantWrite] = []
    specs: list[ProductSpecificationWrite] = []
    customization_rules: list[CustomizationRuleWrite] = []
    related_product_ids: list[int] = []
    tags: list[str] = []


class ProductReviewCreate(BaseModel):
    rating: int
    title: str | None = None
    body: str | None = None


class ProductReviewModerationUpdate(BaseModel):
    status: str | None = None
    admin_reply: str | None = None
    is_spam: bool | None = None


class FilterOptions(BaseModel):
    categories: list[CategoryRead] = Field(default_factory=list)
    sizes: list[str] = Field(default_factory=list)
    colors: list[str] = Field(default_factory=list)
    price_range: dict[str, Decimal] = Field(default_factory=dict)


CategoryTreeRead.model_rebuild()
FilterOptions.model_rebuild()
