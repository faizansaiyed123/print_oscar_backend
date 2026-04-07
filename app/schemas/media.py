from app.schemas.common import TimestampedSchema


class MediaAssetRead(TimestampedSchema):
    id: int
    product_id: int | None = None
    category_id: int | None = None
    file_name: str
    file_path: str
    mime_type: str
    file_size: int
    alt_text: str | None = None
    is_public: bool


class UploadedCustomerFileRead(TimestampedSchema):
    id: int
    order_item_id: int | None = None
    user_id: int | None = None
    product_id: int | None = None
    file_name: str
    file_path: str
    mime_type: str
    file_size: int
    preview_url: str | None = None
    field_type: str
