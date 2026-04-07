from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_roles
from app.schemas.admin import AdminUserCreate, CustomerEmailRequest, RoleRead, RoleWrite
from app.schemas.common import PaginatedResponse
from app.schemas.user import CustomerAdminRead, CustomerAdminUpdate, UserRead
from app.services.admin import AdminService
from app.services.user import UserService

router = APIRouter(dependencies=[Depends(require_roles("super_admin", "admin", "manager"))])


@router.get("/customers", response_model=PaginatedResponse)
async def customers(page: int = 1, page_size: int = 20, search: str | None = None, session: AsyncSession = Depends(get_db)):
    service = UserService(session)
    items, total = await service.list_customers(page=page, page_size=page_size, search=search)
    return PaginatedResponse(items=[CustomerAdminRead.model_validate(item) for item in items], total=total, page=page, page_size=page_size)


@router.patch("/customers/{customer_id}", response_model=CustomerAdminRead)
async def update_customer(customer_id: int, payload: CustomerAdminUpdate, session: AsyncSession = Depends(get_db)) -> CustomerAdminRead:
    service = UserService(session)
    customer = await service.update_customer(customer_id, payload)
    return CustomerAdminRead.model_validate(customer)


@router.post("/customers/{customer_id}/email")
async def email_customer(customer_id: int, payload: CustomerEmailRequest, session: AsyncSession = Depends(get_db)):
    service = AdminService(session)
    return await service.send_email_to_customer(customer_id, payload.subject, payload.body)


@router.post("/customers/{customer_id}/reset-password", response_model=UserRead)
async def reset_customer_password(customer_id: int, new_password: str, session: AsyncSession = Depends(get_db)) -> UserRead:
    service = UserService(session)
    user = await service.reset_customer_password(customer_id, new_password)
    return UserRead.model_validate(user)


@router.get("/roles", response_model=list[RoleRead], dependencies=[Depends(require_roles("super_admin"))])
async def roles(session: AsyncSession = Depends(get_db)) -> list[RoleRead]:
    service = AdminService(session)
    roles_data = await service.list_roles()
    return [RoleRead.model_validate(role) for role in roles_data]



@router.get("/permissions", dependencies=[Depends(require_roles("super_admin"))])
async def permissions(session: AsyncSession = Depends(get_db)):
    service = AdminService(session)
    return await service.list_permissions()



@router.post("/roles", response_model=RoleRead, dependencies=[Depends(require_roles("super_admin"))])
async def create_role(payload: RoleWrite, session: AsyncSession = Depends(get_db)) -> RoleRead:
    service = AdminService(session)
    role = await service.create_role(payload.name, payload.description, payload.permission_ids)
    return RoleRead.model_validate(role)



@router.put("/roles/{role_id}", response_model=RoleRead, dependencies=[Depends(require_roles("super_admin"))])
async def update_role(role_id: int, payload: RoleWrite, session: AsyncSession = Depends(get_db)) -> RoleRead:
    service = AdminService(session)
    role = await service.update_role(role_id, payload.name, payload.description, payload.permission_ids)
    return RoleRead.model_validate(role)



@router.post("/admin-users", response_model=UserRead, dependencies=[Depends(require_roles("super_admin"))])
async def create_admin_user(payload: AdminUserCreate, session: AsyncSession = Depends(get_db)) -> UserRead:
    service = AdminService(session)
    user = await service.create_admin_user(payload)
    return UserRead.model_validate(user)

