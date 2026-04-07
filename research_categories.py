import asyncio
import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.core.config import settings

async def research_categories():
    print(f"Connecting to database: {settings.postgres_db}...")
    engine = create_async_engine(settings.database_url)
    
    async with engine.connect() as conn:
        print("\n--- PRODUCT 145 CATEGORY ---")
        res_p145 = await conn.execute(text("SELECT name FROM categories WHERE id = 503"))
        for r in res_p145.fetchall():
            print(f"ID 503 | Name: {r[0]}")
            
        print("\n--- TOP-LEVEL CATEGORIES ---")
        res_top = await conn.execute(text("SELECT id, name FROM categories WHERE parent_id IS NULL"))
        for r in res_top.fetchall():
            print(f"ID: {r[0]} | Name: {r[1]}")
            
        print("\n--- SAMPLE CATEGORIES IN THE TREE ---")
        res_tree = await conn.execute(text("SELECT id, name, parent_id FROM categories LIMIT 100"))
        for r in res_tree.fetchall():
            print(f"ID: {r[0]} | Name: {r[1]} | Parent: {r[2]}")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(research_categories())
