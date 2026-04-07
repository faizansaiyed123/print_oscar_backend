import asyncio
import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.core.config import settings
from app.services.catalog import CatalogService

async def verify_145_properly():
    print(f"Connecting to database: {settings.postgres_db}...")
    engine = create_async_engine(settings.database_url)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        service = CatalogService(session)
        print("Fetching Product 145...")
        product = await service.get_product(product_id=145)
        
        print(f"\nProduct: {product.title}")
        print("Customization Rules (Resolved):")
        if not product.customization_rules:
            print("  ❌ [NONE FOUND]")
        else:
            for rule in product.customization_rules:
                print(f"  ✅ [{rule.field_type.upper()}] {rule.label}")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(verify_145_properly())
