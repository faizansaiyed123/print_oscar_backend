import asyncio
import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.core.config import settings

async def run_migration():
    print(f"Connecting to database: {settings.postgres_db}...")
    engine = create_async_engine(settings.database_url)
    
    migration_file = "migrations/003_dynamic_customization.sql"
    if not os.path.exists(migration_file):
        print(f"Error: Migration file {migration_file} not found.")
        return

    async with engine.begin() as conn:
        print(f"Reading migration script: {migration_file}...")
        with open(migration_file, "r") as f:
            sql = f.read()
            
        print("Executing migration...")
        # Split by ';' to execute multiple statements if needed, 
        # but sqlalchemy.text(sql) handles the whole block in many cases
        await conn.execute(text(sql))
        print("Migration completed successfully!")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_migration())
