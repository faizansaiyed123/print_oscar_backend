import asyncio
import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.settings import StoreSetting
from sqlalchemy import select

async def check():
    async with SessionLocal() as s:
        result = await s.execute(select(StoreSetting))
        settings = result.scalars().all()
        print("Current Store Settings:")
        for setting in settings:
            print(f"Key: {setting.key}, Value: {setting.value}, Is Public: {setting.is_public}")

if __name__ == "__main__":
    asyncio.run(check())
