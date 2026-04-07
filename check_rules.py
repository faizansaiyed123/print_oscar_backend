import asyncio
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

sys.path.append(os.getcwd())

from app.core.config import settings
from app.models.catalog import ProductCustomizationRule

async def check_rules():
    engine = create_async_engine(settings.database_url)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(ProductCustomizationRule).where(ProductCustomizationRule.product_id == 108))
        rules = result.scalars().all()
        print(f"Found {len(rules)} rules for Product 108")
        for r in rules:
            print(f"- {r.label} ({r.field_type})")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_rules())
