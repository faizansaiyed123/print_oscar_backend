#!/usr/bin/env python3
"""
Script to check admin user status.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.core.config import settings
from app.core.security import verify_password
from app.models.user import User, Role, UserRole


async def check_admin_user():
    """Check admin user status and roles."""
    
    # Database connection
    engine = create_async_engine(settings.database_url)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        try:
            # Check admin user
            result = await session.execute(
                select(User).where(User.email == "admin@trophystore.com")
            )
            admin_user = result.scalar_one_or_none()
            
            if not admin_user:
                print("❌ Admin user not found!")
                return False
            
            print("✅ Admin user found:")
            print(f"   Email: {admin_user.email}")
            print(f"   Active: {admin_user.is_active}")
            print(f"   Verified: {admin_user.is_verified}")
            
            # Check password
            if admin_user.password_hash and verify_password("admin123", admin_user.password_hash):
                print("✅ Password verification: PASSED")
            else:
                print("❌ Password verification: FAILED")
                return False
            
            # Check roles
            result = await session.execute(
                select(Role).join(UserRole).where(UserRole.user_id == admin_user.id)
            )
            roles = result.scalars().all()
            
            print(f"📋 User roles: {[role.name for role in roles]}")
            
            # Check if admin role exists
            admin_role_exists = any(role.name == "admin" for role in roles)
            
            if admin_role_exists:
                print("✅ Admin role: ASSIGNED")
                return True
            else:
                print("❌ Admin role: NOT ASSIGNED")
                
                # Try to assign admin role
                result = await session.execute(
                    select(Role).where(Role.name == "admin")
                )
                admin_role = result.scalar_one_or_none()
                
                if admin_role:
                    user_role = UserRole(
                        user_id=admin_user.id,
                        role_id=admin_role.id
                    )
                    session.add(user_role)
                    await session.commit()
                    print("✅ Admin role assigned successfully!")
                    return True
                else:
                    print("❌ Admin role doesn't exist in database")
                    return False
                    
        except Exception as e:
            print(f"❌ Error checking admin user: {str(e)}")
            return False


async def main():
    """Main function."""
    print("🔍 Checking Admin User Status")
    print("=" * 40)
    
    success = await check_admin_user()
    
    if success:
        print("\n✨ Admin user is ready!")
        print("📋 Login credentials:")
        print("   Email: admin@trophystore.com")
        print("   Password: admin123")
        sys.exit(0)
    else:
        print("\n❌ Admin user setup failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
