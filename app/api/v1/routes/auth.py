from secrets import token_urlsafe

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.rate_limit import InMemoryRateLimiter
from app.schemas.auth import (
    ForgotPasswordRequest,
    GuestSessionCreate,
    LogoutRequest,
    RefreshRequest,
    ResetPasswordRequest,
    TokenPair,
    UserLogin,
    UserRegister,
)
from app.schemas.common import ActionResponse
from app.schemas.user import UserRead
from app.services.auth import AuthService

router = APIRouter()
login_rate_limit = InMemoryRateLimiter(limit=10, window_seconds=60)


@router.post("/register", response_model=UserRead)
async def register(payload: UserRegister, session: AsyncSession = Depends(get_db)) -> UserRead:
    service = AuthService(session)
    user = await service.register(payload)
    return UserRead.model_validate(user)


@router.post("/login", response_model=TokenPair, dependencies=[Depends(login_rate_limit)])
async def login(payload: UserLogin, request: Request, session: AsyncSession = Depends(get_db)) -> TokenPair:
    service = AuthService(session)
    return await service.login(
        payload,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, request: Request, session: AsyncSession = Depends(get_db)) -> TokenPair:
    service = AuthService(session)
    return await service.refresh(
        payload.refresh_token,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )


@router.post("/logout", response_model=ActionResponse)
async def logout(payload: LogoutRequest, session: AsyncSession = Depends(get_db)) -> ActionResponse:
    service = AuthService(session)
    await service.logout(payload.refresh_token)
    return ActionResponse(message="Logged out successfully")


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, session: AsyncSession = Depends(get_db)) -> dict[str, str]:
    service = AuthService(session)
    return await service.forgot_password(payload.email)


@router.post("/reset-password", response_model=ActionResponse)
async def reset_password(payload: ResetPasswordRequest, session: AsyncSession = Depends(get_db)) -> ActionResponse:
    service = AuthService(session)
    await service.reset_password(payload)
    return ActionResponse(message="Password updated successfully")


@router.post("/guest-session")
async def create_guest_session(_: GuestSessionCreate) -> dict[str, str]:
    return {"session_key": token_urlsafe(16)}
