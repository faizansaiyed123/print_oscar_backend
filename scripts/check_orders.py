import asyncio
import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.checkout import Order
from sqlalchemy import select

async def check_orders():
    async with SessionLocal() as s:
        print("Checking recent orders...")
        result = await s.execute(select(Order).order_by(Order.created_at.desc()).limit(5))
        orders = result.scalars().all()
        if not orders:
            print("No orders found in the database.")
        else:
            for o in orders:
                print(f"ID: {o.id}, Order Number: {o.order_number}, Status: {o.status}, Total: {o.total_amount}")

if __name__ == "__main__":
    asyncio.run(check_orders())
