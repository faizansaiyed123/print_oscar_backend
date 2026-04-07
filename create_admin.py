#!/usr/bin/env python3
"""
Script to create an admin user for the trophy store backend.
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
from app.core.security import hash_password
from app.models.user import User, Role, UserRole


async def create_admin_user():
    """Create an admin user with default credentials."""
    
    # Database connection
    engine = create_async_engine(settings.database_url)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        try:
            # Check if admin user already exists
            result = await session.execute(
                select(User).where(User.email == "admin@trophystore.com")
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print("❌ Admin user already exists!")
                print(f"   Email: admin@trophystore.com")
                print("   If you forgot the password, please delete the user and run this script again.")
                return False
            
            # Create admin role if it doesn't exist
            result = await session.execute(
                select(Role).where(Role.name == "admin")
            )
            admin_role = result.scalar_one_or_none()
            
            if not admin_role:
                admin_role = Role(
                    name="admin",
                    description="System administrator with full access"
                )
                session.add(admin_role)
                await session.flush()
                print("✅ Created admin role")
            
            # Create admin user
            admin_user = User(
                email="admin@trophystore.com",
                password_hash=hash_password("admin123"),
                first_name="Admin",
                last_name="User",
                is_active=True,
                is_verified=True,
                is_guest=False,
            )
            
            session.add(admin_user)
            await session.flush()
            print("✅ Created admin user")
            
            # Assign admin role to user
            user_role = UserRole(
                user_id=admin_user.id,
                role_id=admin_role.id
            )
            session.add(user_role)
            
            await session.commit()
            
            print("\n🎉 Admin user created successfully!")
            print("\n📋 Login Credentials:")
            print("   Email:    admin@trophystore.com")
            print("   Password: admin123")
            print("\n🔐 Please change the password after first login!")
            print("\n🌐 You can now:")
            print("   1. Start the server: uvicorn app.main:app --reload")
            print("   2. Visit: http://localhost:8000/docs")
            print("   3. Login with admin credentials")
            print("   4. Access admin endpoints")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating admin user: {str(e)}")
            await session.rollback()
            return False


async def main():
    """Main function."""
    print("🚀 Creating Admin User for Trophy Store Backend")
    print("=" * 50)
    
    success = await create_admin_user()
    
    if success:
        print("\n✨ Setup completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Setup failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
