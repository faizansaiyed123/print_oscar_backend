import asyncio
import os
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.settings import StoreSetting
from sqlalchemy import select

async def make_site_logo_public():
    async with SessionLocal() as s:
        # Find the existing site_logo key already in the database
        result = await s.execute(select(StoreSetting).where(StoreSetting.key == 'site_logo'))
        site_logo = result.scalar_one_or_none()

        if site_logo:
            site_logo.is_public = True
            print(f"SUCCESS: 'site_logo' marked as public. Value: {site_logo.value}")
        else:
            print("WARNING: 'site_logo' key not found in the database.")
            print("Please add it via the admin panel: PUT /api/v1/admin/settings")
            print('  Body: {"key": "site_logo", "value": "<your-logo-url>", "is_public": true}')

        await s.commit()

if __name__ == "__main__":
    asyncio.run(make_site_logo_public())
