#!/usr/bin/env python3
"""
Script to test admin login.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import httpx


async def test_login():
    """Test admin login via HTTP request."""
    
    # API base URL
    base_url = "http://localhost:8000/api/v1"
    
    async with httpx.AsyncClient() as client:
        try:
            # Test login
            login_data = {
                "email": "admin@trophystore.com",
                "password": "admin123"
            }
            
            print("🔐 Testing admin login...")
            print(f"   URL: {base_url}/auth/login")
            print(f"   Data: {login_data}")
            
            response = await client.post(f"{base_url}/auth/login", json=login_data)
            
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            
            if response.status_code == 200:
                print("✅ Login successful!")
                token_data = response.json()
                print(f"   Access token: {token_data.get('access_token', '')[:50]}...")
                return True
            else:
                print("❌ Login failed!")
                return False
                
        except httpx.ConnectError:
            print("❌ Cannot connect to server!")
            print("   Make sure the server is running: uvicorn app.main:app --reload")
            return False
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False


async def main():
    """Main function."""
    print("🧪 Testing Admin Login")
    print("=" * 30)
    
    success = await test_login()
    
    if success:
        print("\n✨ Login test passed!")
        print("📋 Your frontend should be able to login with:")
        print("   Email: admin@trophystore.com")
        print("   Password: admin123")
        print("   Endpoint: POST /api/v1/auth/login")
    else:
        print("\n❌ Login test failed!")
        print("🔧 Troubleshooting:")
        print("   1. Make sure server is running: uvicorn app.main:app --reload")
        print("   2. Check server logs for errors")
        print("   3. Verify database connection")
        print("   4. Check if admin user exists")


if __name__ == "__main__":
    asyncio.run(main())
