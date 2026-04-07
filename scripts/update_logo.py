import asyncio
import os
import sys

sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.settings import StoreSetting
from sqlalchemy import select

async def update_logo(real_url: str):
    async with SessionLocal() as s:
        result = await s.execute(select(StoreSetting).where(StoreSetting.key == 'site_logo'))
        setting = result.scalar_one_or_none()
        if setting:
            setting.value = real_url
            setting.is_public = True
            print(f"Updated site_logo to: {real_url}")
        else:
            s.add(StoreSetting(key='site_logo', value=real_url, is_public=True))
            print(f"Created site_logo with: {real_url}")
        await s.commit()

if __name__ == "__main__":
    # PASTE YOUR REAL LOGO URL BELOW
    real_logo_url = "PASTE_YOUR_REAL_LOGO_URL_HERE"
    asyncio.run(update_logo(real_logo_url))
