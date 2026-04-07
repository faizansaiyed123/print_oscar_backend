import asyncio
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add the project root to sys.path to import app modules
import os
sys.path.append(os.getcwd())

from app.core.config import settings
from app.models.catalog import Product, ProductCustomizationRule

async def add_test_rules():
    engine = create_async_engine(settings.database_url)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        # Find Product 108
        result = await session.execute(select(Product).where(Product.id == 108))
        product = result.scalar_one_or_none()
        
        if not product:
            print("Product 108 not found!")
            return

        print(f"Adding rules to: {product.title}")
        
        # Clear existing rules if any
        from sqlalchemy import delete
        await session.execute(delete(ProductCustomizationRule).where(ProductCustomizationRule.product_id == 108))
        
        # Add Rules
        rules = [
            ProductCustomizationRule(
                product_id=108,
                field_type="file",
                label="Upload Your Logo",
                is_required=True,
                help_text="Please upload a high-resolution PNG or SVG logo.",
                validation_rules={"allowed_extensions": ["png", "svg", "jpg"], "max_size_mb": 5}
            ),
            ProductCustomizationRule(
                product_id=108,
                field_type="text",
                label="Engraving Text",
                is_required=False,
                help_text="Enter the text you want engraved on the plate.",
                validation_rules={"max_length": 50}
            ),
             ProductCustomizationRule(
                product_id=108,
                field_type="dropdown",
                label="Plate Material",
                is_required=True,
                validation_rules={"options": ["Gold Acrylic", "Silver Acrylic", "Brass Plate"]}
            )
        ]
        
        session.add_all(rules)
        await session.commit()
        print("Successfully added 3 dynamic customization rules to Product 108.")
        
    await engine.dispose()

if __name__ == "__main__":
    try:
        asyncio.run(add_test_rules())
    except Exception as e:
        print(f"Error: {e}")
