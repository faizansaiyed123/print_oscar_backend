import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.core.config import settings
from app.services.catalog import CatalogService

async def verify_intelligent_resolver():
    print(f"Connecting to database: {settings.postgres_db}...")
    engine = create_async_engine(settings.database_url)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        service = CatalogService(session)
        
        # Test Products
        test_ids = [108, 145]
        
        for pid in test_ids:
            print(f"\n--- Checking Product ID: {pid} ---")
            try:
                product = await service.get_product(product_id=pid)
                print(f"Title: {product.title}")
                print(f"Category: {product.primary_category.name if product.primary_category else 'None'}")
                print("Customization Rules Detected:")
                if not product.customization_rules:
                    print("  ❌ [NONE FOUND]")
                else:
                    for rule in product.customization_rules:
                        print(f"  ✅ [{rule.field_type.upper()}] {rule.label}")
            except Exception as e:
                print(f"  Error fetching product {pid}: {e}")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(verify_intelligent_resolver())
