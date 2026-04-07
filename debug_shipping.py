import asyncio
import sys
import os

# Adjust sys.path to include the project root
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models.operations import ShippingMethod
from sqlalchemy import select

async def check():
    async with SessionLocal() as s:
        r = await s.execute(select(ShippingMethod.code, ShippingMethod.name))
        methods = r.fetchall()
        print("Available Shipping Methods:")
        for code, name in methods:
            print(f"- {code}: {name}")

if __name__ == "__main__":
    asyncio.run(check())
