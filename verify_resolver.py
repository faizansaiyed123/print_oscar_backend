import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.core.config import settings
from app.services.catalog import CatalogService

async def verify_108():
    print(f"Connecting to database: {settings.postgres_db}...")
    engine = create_async_engine(settings.database_url)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        service = CatalogService(session)
        print("Fetching Product 108...")
        product = await service.get_product(product_id=108)
        
        print(f"\nProduct: {product.title}")
        print(f"Slug: {product.metadata_record.slug if product.metadata_record else 'N/A'}")
        print("\nDynamic Customization Rules Found:")
        if not product.customization_rules:
            print("  (Empty - Resolver failed)")
        else:
            for rule in product.customization_rules:
                print(f"  - [{rule.field_type.upper()}] {rule.label} (Required: {rule.is_required})")
                if rule.help_text:
                    print(f"    Help: {rule.help_text}")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(verify_108())
