import asyncio
import os
import sys
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.core.config import settings
from app.models.catalog import Product

async def research_products():
    engine = create_async_engine(settings.database_url)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        # Look for typical customization keywords
        stmt = select(Product).where(
            or_(
                Product.title.ilike("%logo%"),
                Product.content.ilike("%logo%"),
                Product.title.ilike("%text%"),
                Product.content.ilike("%text%"),
                Product.title.ilike("%plaque%"),
                Product.title.ilike("%engrav%"),
                Product.content.ilike("%engrav%")
            )
        ).limit(10)
        
        result = await session.execute(stmt)
        products = result.scalars().all()
        
        print(f"--- Research: Found {len(products)} products that might need customization ---")
        for p in products:
            print(f"ID: {p.id}")
            print(f"Title: {p.title}")
            print(f"Content (snippet): {p.content[:100]}...")
            print("-" * 30)
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(research_products())
