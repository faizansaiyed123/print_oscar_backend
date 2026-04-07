from pydantic import BaseModel

from app.schemas.common import TimestampedSchema


class NewsletterSubscriberRead(TimestampedSchema):
    id: int
    email: str
    is_active: bool


class PublicSettingRead(BaseModel):
    key: str
    value: str

    class Config:
        from_attributes = True


class BannerRead(TimestampedSchema):
    id: int
    title: str
    image_url: str
    target_url: str | None = None
    is_active: bool
