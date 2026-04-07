import os
import sys
import psycopg2

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.core.config import settings

def run_migration():
    print(f"Connecting to database: {settings.postgres_db}...")
    try:
        # Connect using sync psycopg2
        conn = psycopg2.connect(
            dbname=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password,
            host=settings.postgres_host,
            port=settings.postgres_port
        )
        conn.autocommit = True
        
        migration_file = "migrations/003_dynamic_customization.sql"
        if not os.path.exists(migration_file):
            print(f"Error: Migration file {migration_file} not found.")
            return

        with open(migration_file, "r") as f:
            sql = f.read()
            
        with conn.cursor() as cur:
            print("Executing migration...")
            cur.execute(sql)
            print("Migration completed successfully!")
            
        conn.close()
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    run_migration()
