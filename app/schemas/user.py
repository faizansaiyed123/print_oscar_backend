from pydantic import BaseModel, EmailStr

from app.schemas.common import ORMModel, TimestampedSchema


class AddressBase(BaseModel):
    address_type: str
    label: str | None = None
    first_name: str
    last_name: str
    email: EmailStr | None = None
    phone_number: str | None = None
    street_address: str
    apartment: str | None = None
    city: str
    state: str
    zip_code: str
    country_code: str = "US"
    is_default: bool = False
    delivery_notes: str | None = None


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    address_type: str | None = None
    label: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone_number: str | None = None
    street_address: str | None = None
    apartment: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    country_code: str | None = None
    is_default: bool | None = None
    delivery_notes: str | None = None


class AddressRead(AddressBase, TimestampedSchema):
    id: int


class UserRead(TimestampedSchema):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    phone_number: str | None = None
    is_active: bool
    is_verified: bool
    is_guest: bool
    marketing_opt_in: bool
    addresses: list[AddressRead] = []


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    marketing_opt_in: bool | None = None


class CustomerAdminRead(UserRead):
    blocked_reason: str | None = None


class CustomerAdminUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    is_active: bool | None = None
    blocked_reason: str | None = None
    marketing_opt_in: bool | None = None
