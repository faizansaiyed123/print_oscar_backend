import asyncio
import os
import sys
from decimal import Decimal

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.operations import ShippingMethod
from sqlalchemy import select

async def seed():
    async with SessionLocal() as s:
        # Check if already exists
        result = await s.execute(select(ShippingMethod).where(ShippingMethod.code == "standard"))
        if result.scalar_one_or_none():
            print("Standard shipping already exists.")
        else:
            method = ShippingMethod(
                code="standard",
                name="Standard Shipping",
                base_rate=Decimal("10.00"),
                estimated_days=5,
                is_enabled=True
            )
            s.add(method)
            print("Added Standard Shipping.")

        result = await s.execute(select(ShippingMethod).where(ShippingMethod.code == "express"))
        if result.scalar_one_or_none():
            print("Express shipping already exists.")
        else:
            method = ShippingMethod(
                code="express",
                name="Express Shipping",
                base_rate=Decimal("25.00"),
                estimated_days=2,
                is_enabled=True
            )
            s.add(method)
            print("Added Express Shipping.")
            
        await s.commit()

if __name__ == "__main__":
    asyncio.run(seed())
