import asyncio
import sys

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import SessionLocal
from app.models.user import Role, User


async def make_superadmin(email: str):
    async with SessionLocal() as session:
        # Find the user by email
        result = await session.execute(
            select(User).options(selectinload(User.roles)).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"Error: User with email '{email}' not found.")
            return

        # Ensure the super_admin role exists
        role_result = await session.execute(select(Role).where(Role.name == "super_admin"))
        role = role_result.scalar_one_or_none()
        
        if not role:
            # Create the role if it doesn't exist
            role = Role(name="super_admin", description="Super Administrator")
            session.add(role)
            await session.flush()
            print("Created 'super_admin' role in database.")

        # Assign the role if the user doesn't already have it
        if any(r.name == "super_admin" for r in user.roles):
            print(f"User '{email}' is already a super_admin.")
        else:
            user.roles.append(role)
            await session.commit()
            print(f"Success! User '{email}' has been promoted to super_admin.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/make_superadmin.py <user_email>")
        sys.exit(1)
    
    email_arg = sys.argv[1]
    asyncio.run(make_superadmin(email_arg))
