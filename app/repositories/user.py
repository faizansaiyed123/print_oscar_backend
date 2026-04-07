from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.models.user import Address, PasswordResetToken, Permission, RefreshToken, Role, User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    async def get_by_id(self, user_id: int) -> User | None:
        statement = (
            select(User)
            .options(
                selectinload(User.roles).selectinload(Role.permissions),
                selectinload(User.addresses),
                selectinload(User.refresh_tokens),
            )
            .where(User.id == user_id)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        statement = (
            select(User)
            .options(
                selectinload(User.roles).selectinload(Role.permissions),
                selectinload(User.addresses),
            )
            .where(User.email == email)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_users(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        is_active: bool | None = None,
        include_guests: bool = True,
    ):
        statement = select(User).options(selectinload(User.roles), selectinload(User.addresses)).order_by(User.created_at.desc())
        if search:
            pattern = f"%{search}%"
            statement = statement.where(
                or_(
                    User.email.ilike(pattern),
                    User.first_name.ilike(pattern),
                    User.last_name.ilike(pattern),
                )
            )
        if is_active is not None:
            statement = statement.where(User.is_active.is_(is_active))
        if not include_guests:
            statement = statement.where(User.is_guest.is_(False))
        return await self.paginate(statement, page=page, page_size=page_size)

    async def get_address(self, address_id: int, user_id: int | None = None) -> Address | None:
        statement = select(Address).where(Address.id == address_id)
        if user_id is not None:
            statement = statement.where(Address.user_id == user_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_addresses(self, user_id: int) -> list[Address]:
        result = await self.session.execute(select(Address).where(Address.user_id == user_id).order_by(Address.is_default.desc(), Address.id.desc()))
        return result.scalars().all()

    async def list_roles(self) -> list[Role]:
        result = await self.session.execute(select(Role).options(selectinload(Role.permissions)).order_by(Role.name.asc()))
        return result.scalars().all()

    async def get_role(self, role_id: int) -> Role | None:
        result = await self.session.execute(select(Role).options(selectinload(Role.permissions)).where(Role.id == role_id))
        return result.scalar_one_or_none()

    async def get_roles_by_ids(self, role_ids: list[int]) -> list[Role]:
        if not role_ids:
            return []
        result = await self.session.execute(select(Role).where(Role.id.in_(role_ids)))
        return result.scalars().all()

    async def list_permissions(self) -> list[Permission]:
        result = await self.session.execute(select(Permission).order_by(Permission.name.asc()))
        return result.scalars().all()

    async def get_permissions_by_ids(self, permission_ids: list[int]) -> list[Permission]:
        if not permission_ids:
            return []
        result = await self.session.execute(select(Permission).where(Permission.id.in_(permission_ids)))
        return result.scalars().all()

    async def get_refresh_token(self, token_hash: str) -> RefreshToken | None:
        result = await self.session.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        return result.scalar_one_or_none()

    async def get_password_reset_token(self, token_hash: str) -> PasswordResetToken | None:
        result = await self.session.execute(select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash))
        return result.scalar_one_or_none()

