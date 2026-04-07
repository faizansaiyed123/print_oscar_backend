from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.exceptions import AppException
from app.core.security import hash_password
from app.models.user import Address, Role, User, Wishlist
from app.models.catalog import Product
from app.repositories.user import UserRepository
from app.schemas.user import AddressCreate, AddressUpdate, CustomerAdminUpdate
from app.schemas.catalog import ProductRead


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = UserRepository(session)

    async def get_profile(self, user_id: int) -> User:
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise AppException("User not found", 404)
        return user

    async def update_profile(self, user: User, payload: dict) -> User:
        for field in ("first_name", "last_name", "phone_number", "marketing_opt_in"):
            if field in payload and payload[field] is not None:
                setattr(user, field, payload[field])
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def list_addresses(self, user_id: int) -> list[Address]:
        return await self.repository.list_addresses(user_id)

    async def create_address(self, user_id: int, payload: AddressCreate) -> Address:
        address = Address(user_id=user_id, **payload.model_dump())
        if payload.is_default:
            await self._clear_default_address(user_id, payload.address_type)
        await self.repository.save(address)
        await self.session.commit()
        await self.session.refresh(address)
        return address

    async def update_address(self, user_id: int, address_id: int, payload: AddressUpdate) -> Address:
        address = await self.repository.get_address(address_id, user_id)
        if not address:
            raise AppException("Address not found", 404)
        data = payload.model_dump(exclude_none=True)
        if data.get("is_default"):
            await self._clear_default_address(user_id, data.get("address_type", address.address_type))
        for field, value in data.items():
            setattr(address, field, value)
        await self.session.commit()
        await self.session.refresh(address)
        return address

    async def delete_address(self, user_id: int, address_id: int) -> None:
        address = await self.repository.get_address(address_id, user_id)
        if not address:
            raise AppException("Address not found", 404)
        await self.repository.delete(address)
        await self.session.commit()

    async def list_customers(self, page: int = 1, page_size: int = 20, search: str | None = None):
        return await self.repository.list_users(page=page, page_size=page_size, search=search, include_guests=False)

    async def update_customer(self, customer_id: int, payload: CustomerAdminUpdate) -> User:
        customer = await self.repository.get_by_id(customer_id)
        if not customer:
            raise AppException("Customer not found", 404)
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(customer, field, value)
        await self.session.commit()
        await self.session.refresh(customer)
        return customer

    async def reset_customer_password(self, customer_id: int, new_password: str) -> User:
        customer = await self.repository.get_by_id(customer_id)
        if not customer:
            raise AppException("Customer not found", 404)
        customer.password_hash = hash_password(new_password)
        customer.is_guest = False
        await self.session.commit()
        await self.session.refresh(customer)
        return customer

    async def assign_roles(self, user: User, role_ids: list[int]) -> User:
        roles = await self.repository.get_roles_by_ids(role_ids)
        user.roles = roles
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def create_admin_user(
        self,
        *,
        email: str,
        password_hash: str,
        first_name: str,
        last_name: str,
        phone_number: str | None,
        role_ids: list[int],
    ) -> User:
        existing = await self.repository.get_by_email(email)
        if existing:
            raise AppException("Email already exists", 400)
        user = User(
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            is_guest=False,
        )
        roles = await self.repository.get_roles_by_ids(role_ids)
        if roles:
            user.roles = roles
        await self.repository.save(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def create_role(self, name: str, description: str | None, permission_ids: list[int]) -> Role:
        role = Role(name=name, description=description)
        role.permissions = await self.repository.get_permissions_by_ids(permission_ids)
        await self.repository.save(role)
        await self.session.commit()
        await self.session.refresh(role)
        return role

    async def update_role(self, role_id: int, name: str | None, description: str | None, permission_ids: list[int] | None) -> Role:
        role = await self.repository.get_role(role_id)
        if not role:
            raise AppException("Role not found", 404)
        if name is not None:
            role.name = name
        if description is not None:
            role.description = description
        if permission_ids is not None:
            role.permissions = await self.repository.get_permissions_by_ids(permission_ids)
        await self.session.commit()
        await self.session.refresh(role)
        return role

    async def _clear_default_address(self, user_id: int, address_type: str) -> None:
        addresses = await self.repository.list_addresses(user_id)
        for address in addresses:
            if address.address_type == address_type and address.is_default:
                address.is_default = False

    async def get_wishlist(self, user_id: int) -> list[Product]:
        result = await self.session.execute(
            select(Product)
            .join(Wishlist, Wishlist.product_id == Product.id)
            .where(Wishlist.user_id == user_id)
        )
        return result.scalars().all()

    async def add_to_wishlist(self, user_id: int, product_id: int) -> Product:
        # Check if product exists
        product_result = await self.session.execute(select(Product).where(Product.id == product_id))
        product = product_result.scalar_one_or_none()
        if not product:
            raise AppException("Product not found", 404)
        
        # Check if already in wishlist
        existing_result = await self.session.execute(
            select(Wishlist).where(Wishlist.user_id == user_id, Wishlist.product_id == product_id)
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            raise AppException("Product already in wishlist", 400)
        
        # Add to wishlist
        wishlist_item = Wishlist(user_id=user_id, product_id=product_id)
        self.session.add(wishlist_item)
        await self.session.commit()
        return product

    async def remove_from_wishlist(self, user_id: int, product_id: int) -> None:
        result = await self.session.execute(
            select(Wishlist).where(Wishlist.user_id == user_id, Wishlist.product_id == product_id)
        )
        wishlist_item = result.scalar_one_or_none()
        if not wishlist_item:
            raise AppException("Product not found in wishlist", 404)
        
        await self.session.delete(wishlist_item)
        await self.session.commit()
