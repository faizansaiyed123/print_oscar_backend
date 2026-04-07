import asyncio
import os
import sys

sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.settings import StoreSetting
from sqlalchemy import delete

async def cleanup():
    async with SessionLocal() as s:
        # Delete the fake logo_url entry
        await s.execute(delete(StoreSetting).where(StoreSetting.key == 'logo_url'))
        await s.commit()
        print("Deleted fake 'logo_url' entry.")

if __name__ == "__main__":
    asyncio.run(cleanup())
