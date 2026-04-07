from datetime import timezone, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.models.user import PasswordResetToken, RefreshToken, Role, User
from app.repositories.user import UserRepository
from app.schemas.auth import ResetPasswordRequest, TokenPair, UserLogin, UserRegister


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)

    async def _ensure_role(self, role_name: str, description: str) -> Role:
        result = await self.session.execute(select(Role).where(Role.name == role_name))
        role = result.scalar_one_or_none()
        if role:
            return role

        role = Role(name=role_name, description=description)
        self.session.add(role)
        await self.session.flush()
        return role

    async def _issue_token_pair(
        self,
        user: User,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
        revoke_refresh_hash: str | None = None,
    ) -> TokenPair:

        if revoke_refresh_hash:
            existing = await self.users.get_refresh_token(revoke_refresh_hash)
            if existing and existing.revoked_at is None:
                existing.revoked_at = datetime.now(timezone.utc)

        access_token = create_token(user.id, "access", settings.access_token_expire_minutes)
        refresh_token = create_token(user.id, "refresh", settings.refresh_token_expire_minutes)

        self.session.add(
            RefreshToken(
                user_id=user.id,
                token_hash=sha256(refresh_token.encode()).hexdigest(),
                expires_at=datetime.now(timezone.utc)
                + timedelta(minutes=settings.refresh_token_expire_minutes),
                user_agent=user_agent,
                ip_address=ip_address,
            )
        )

        user.last_login_at = datetime.now(timezone.utc)
        await self.session.flush()

        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    async def register(self, payload: UserRegister) -> User:
        existing = await self.users.get_by_email(payload.email)
        if existing:
            raise AppException("Email already exists")

        customer_role = await self._ensure_role("customer", "Store customer role")

        user = User(
            email=payload.email,
            password_hash=hash_password(payload.password),
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone_number=payload.phone_number,
            marketing_opt_in=getattr(payload, "marketing_opt_in", False),
        )

        user.roles.append(customer_role)

        await self.users.save(user)
        await self.session.commit()

        user = await self.users.get_by_id(user.id)
        return user

    async def login(
        self,
        payload: UserLogin,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> TokenPair:

        # ✅ load user WITH roles
        user = await self.users.get_by_email(payload.email)

        if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
            raise AppException("Invalid credentials", 401)

        if not user.is_active:
            raise AppException("User account is disabled", 403)

        # ✅ ADMIN CHECK
        role_names = [role.name for role in user.roles]

        if "admin" not in role_names and "super_admin" not in role_names:
            raise AppException("Admin access required", 403)

        token_pair = await self._issue_token_pair(
            user,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        await self.session.commit()
        return token_pair

    async def refresh(
        self,
        refresh_token: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> TokenPair:

        try:
            payload = decode_token(refresh_token)
        except ValueError as exc:
            raise AppException("Invalid refresh token", 401) from exc

        if payload.get("type") != "refresh":
            raise AppException("Invalid refresh token", 401)

        token_hash = sha256(refresh_token.encode()).hexdigest()
        stored_token = await self.users.get_refresh_token(token_hash)

        if (
            not stored_token
            or stored_token.revoked_at is not None
            or stored_token.expires_at <= datetime.now(timezone.utc)
        ):
            raise AppException("Refresh token expired or revoked", 401)

        user = await self.users.get_by_id(int(payload["sub"]))

        if not user or not user.is_active:
            raise AppException("User unavailable", 401)

        token_pair = await self._issue_token_pair(
            user,
            user_agent=user_agent,
            ip_address=ip_address,
            revoke_refresh_hash=token_hash,
        )

        await self.session.commit()
        return token_pair

    async def logout(self, refresh_token: str) -> None:
        token_hash = sha256(refresh_token.encode()).hexdigest()
        stored_token = await self.users.get_refresh_token(token_hash)

        if stored_token:
            stored_token.revoked_at = datetime.now(timezone.utc)
            await self.session.commit()

    async def forgot_password(self, email: str) -> dict[str, str]:
        user = await self.users.get_by_email(email)

        if not user:
            return {"message": "If the email exists, a reset token has been generated."}

        raw_token = token_urlsafe(32)
        hashed = sha256(raw_token.encode()).hexdigest()

        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=hashed,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
        )

        self.session.add(reset_token)
        await self.session.commit()

        return {
            "message": "Password reset token generated.",
            "reset_token": raw_token,
        }

    async def reset_password(self, payload: ResetPasswordRequest) -> None:
        token_hash = sha256(payload.token.encode()).hexdigest()
        reset_token = await self.users.get_password_reset_token(token_hash)

        if (
            not reset_token
            or reset_token.used_at is not None
            or reset_token.expires_at <= datetime.now(timezone.utc)
        ):
            raise AppException("Reset token is invalid or expired", 400)

        user = await self.users.get_by_id(reset_token.user_id)

        if not user:
            raise AppException("User unavailable", 404)

        user.password_hash = hash_password(payload.new_password)
        user.is_guest = False
        reset_token.used_at = datetime.now(timezone.utc)

        await self.session.commit()