
import asyncio
from app.db.session import SessionLocal
from app.models.user import User, Role
from sqlalchemy import select
from app.core.security import hash_password

async def setup():
    async with SessionLocal() as session:
        # Check if any user exists
        res = await session.execute(select(User))
        user = res.scalars().first()
        if not user:
            # Create a super admin
            admin_role = Role(name="super_admin", description="Super Admin")
            session.add(admin_role)
            await session.flush()
            
            admin_user = User(
                email="admin@example.com",
                password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGGa31S.",
                first_name="Admin",
                last_name="User",
                is_active=True,
                is_verified=True,
                is_guest=False
            )
            admin_user.roles = [admin_role]
            session.add(admin_user)
            await session.commit()
            print("CREATED_ADMIN: admin@example.com / admin123")
        else:
            print(f"EXISTING_USER: {user.email}")
            # Ensure it has super_admin role for testing
            admin_role_res = await session.execute(select(Role).where(Role.name == "super_admin"))
            admin_role = admin_role_res.scalars().first()
            if not admin_role:
                admin_role = Role(name="super_admin", description="Super Admin")
                session.add(admin_role)
                await session.flush()
            
            if admin_role not in user.roles:
                user.roles.append(admin_role)
                await session.commit()
            print(f"USER {user.email} IS NOW SUPER_ADMIN")

if __name__ == "__main__":
    asyncio.run(setup())
