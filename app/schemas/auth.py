from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMModel


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str
    last_name: str
    phone_number: str | None = None
    marketing_opt_in: bool = False


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenPair(ORMModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class LogoutRequest(BaseModel):
    refresh_token: str


class GuestSessionCreate(BaseModel):
    email: EmailStr | None = None
