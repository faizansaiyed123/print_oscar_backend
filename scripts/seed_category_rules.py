import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.catalog import Category, CategoryCustomizationRule

async def seed_category_rules():
    engine = create_async_engine(settings.database_url)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        # 1. Identity key categories by name
        # We search for common keywords in category names to apply rules
        stmt = select(Category)
        result = await session.execute(stmt)
        categories = result.scalars().all()
        
        award_keywords = ["plaque", "award", "trophy", "medal", "cup", "gift", "frame"]
        
        # Rules to apply
        engraving_rule_data = {
            "field_type": "text",
            "label": "Engraving Text",
            "is_required": False,
            "help_text": "Enter the text you want engraved (optional).",
            "validation_rules": {"max_length": 250},
            "is_enabled": True
        }
        
        logo_rule_data = {
            "field_type": "file",
            "label": "Upload Your Logo",
            "is_required": False,
            "help_text": "Please upload your logo file (PNG, SVG, or JPG).",
            "allowed_file_types": ["image/png", "image/jpeg", "image/svg+xml", "application/pdf"],
            "max_file_size_mb": 5,
            "is_enabled": True
        }
        
        count = 0
        for cat in categories:
            cat_name = cat.name.lower()
            if any(k in cat_name for k in award_keywords):
                print(f"Applying rules to category: {cat.name} (ID: {cat.id})")
                
                # Check if rules already exist to avoid duplicates
                stmt_check = select(CategoryCustomizationRule).where(
                    CategoryCustomizationRule.category_id == cat.id
                )
                res_check = await session.execute(stmt_check)
                existing = res_check.scalars().all()
                labels = {r.label.lower() for r in existing}
                
                if "engraving text" not in labels:
                    session.add(CategoryCustomizationRule(category_id=cat.id, **engraving_rule_data))
                    count += 1
                
                if "upload your logo" not in labels:
                    session.add(CategoryCustomizationRule(category_id=cat.id, **logo_rule_data))
                    count += 1
        
        await session.commit()
        print(f"Successfully seeded {count} category customization rules.")
    
    # Clean up
    await engine.dispose()

if __name__ == "__main__":
    try:
        asyncio.run(seed_category_rules())
    except Exception as e:
        print(f"Error: {e}")
