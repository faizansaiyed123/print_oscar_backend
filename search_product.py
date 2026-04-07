import asyncio
import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.core.config import settings

async def find_product(keyword):
    print(f"Connecting to database: {settings.postgres_db}...")
    engine = create_async_engine(settings.database_url)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        print(f"Searching for products related to '{keyword}'...")
        query = text("""
            SELECT p.id, p.title, pm.slug 
            FROM products p 
            JOIN product_meta pm ON p.id = pm.product_id 
            WHERE p.title ILIKE :kw OR pm.slug ILIKE :kw
        """)
        result = await session.execute(query, {"kw": f"%{keyword}%"})
        products = result.fetchall()
        
        if not products:
            print(f"  ❌ No products found matching '{keyword}'.")
        else:
            print(f"\n--- Found {len(products)} Product(s) ---")
            for r in products:
                print(f"ID: {r[0]} | Title: {r[1]} | Slug: {r[2]}")
            
    await engine.dispose()

if __name__ == "__main__":
    kw = sys.argv[1] if len(sys.argv) > 1 else "hockey"
    asyncio.run(find_product(kw))
