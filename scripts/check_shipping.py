import asyncio
import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from sqlalchemy import text

async def check():
    async with SessionLocal() as s:
        print("Checking shipping methods...")
        result = await s.execute(text("SELECT id, code, name FROM shipping_methods"))
        methods = result.fetchall()
        if not methods:
            print("No shipping methods found in the database.")
        else:
            for m in methods:
                print(f"ID: {m[0]}, Code: {m[1]}, Name: {m[2]}")

if __name__ == "__main__":
    asyncio.run(check())
