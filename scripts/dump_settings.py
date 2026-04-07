import asyncio
import os
import sys

sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.settings import StoreSetting
from sqlalchemy import select, text

async def check_all():
    async with SessionLocal() as s:
        # Use raw SQL to see exact data
        result = await s.execute(text("SELECT key, value, is_public FROM store_settings"))
        rows = result.fetchall()
        print("=== ALL ROWS IN store_settings TABLE ===")
        for row in rows:
            print(f"  key={row[0]!r}  |  value={row[1]!r}  |  is_public={row[2]}")
        print(f"=== TOTAL: {len(rows)} rows ===")

if __name__ == "__main__":
    asyncio.run(check_all())
