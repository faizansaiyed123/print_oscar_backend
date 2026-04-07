import asyncio
import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.core.config import settings

async def research_patterns():
    print(f"Connecting to database: {settings.postgres_db}...")
    engine = create_async_engine(settings.database_url)
    
    async with engine.connect() as conn:
        print("\n--- TOP CATEGORIES ---")
        res_cat = await conn.execute(text("SELECT id, name FROM categories ORDER BY name LIMIT 50"))
        for r in res_cat.fetchall():
            print(f"ID: {r[0]} | Name: {r[1]}")
            
        print("\n--- SAMPLE PRODUCTS BY SKU AND TITLE ---")
        res_prod = await conn.execute(text("""
            SELECT id, title, sku, category_id 
            FROM products 
            WHERE category_id IS NOT NULL 
            LIMIT 50
        """))
        for r in res_prod.fetchall():
            print(f"ID: {r[0]} | SKU: {r[2]} | CatID: {r[3]} | Title: {r[1]}")
            
        print("\n--- PRODUCTS MENTIONING 'LOGO' OR 'ENGRAVING' ---")
        res_kw = await conn.execute(text("""
            SELECT id, title 
            FROM products 
            WHERE title ILIKE '%logo%' OR content ILIKE '%logo%' OR title ILIKE '%engrav%' OR content ILIKE '%engrav%'
            LIMIT 20
        """))
        for r in res_kw.fetchall():
            print(f"ID: {r[0]} | Title: {r[1]}")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(research_patterns())
