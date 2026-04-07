import asyncio
import os
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.settings import StoreSetting
from sqlalchemy import select

async def update_key():
    async with SessionLocal() as s:
        # Check if site_logo exists
        result = await s.execute(select(StoreSetting).where(StoreSetting.key == 'site_logo'))
        site_logo = result.scalar_one_or_none()
        
        if not site_logo:
            # Create site_logo using the existing logo_url value if it exists
            res_old = await s.execute(select(StoreSetting).where(StoreSetting.key == 'logo_url'))
            logo_url = res_old.scalar_one_or_none()
            
            val = logo_url.value if logo_url else "https://example.com/logo.png"
            site_logo = StoreSetting(key='site_logo', value=val, is_public=True)
            s.add(site_logo)
            print(f"Created 'site_logo' with value: {val}")
        else:
            site_logo.is_public = True
            print("'site_logo' already exists, ensured it is public.")
            
        await s.commit()

if __name__ == "__main__":
    asyncio.run(update_key())
