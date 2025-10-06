"""
Test script to verify Supabase database connection.
Run this after setting up your .env file with DATABASE_URL.

Usage:
    python test_db_connection.py
"""

import asyncio
import os
from dotenv import load_dotenv
from src.database import init_db_pool, close_db_pool, fetch_one, fetch_all, insert_one, execute

# Load environment variables
load_dotenv()


async def test_connection():
    """Test basic database connection and operations."""
    
    print("=" * 60)
    print("Testing Supabase Database Connection")
    print("=" * 60)
    
    try:
        # 1. Initialize connection pool
        print("\n1. Initializing database connection pool...")
        await init_db_pool()
        print("   ✓ Connection pool initialized successfully")
        
        # 2. Test simple query - check PostgreSQL version
        print("\n2. Testing basic query (PostgreSQL version)...")
        result = await fetch_one("SELECT version()")
        if result:
            version = result['version']
            print(f"   ✓ Connected to: {version[:60]}...")
        
        # 3. Test table existence - check if schema is applied
        print("\n3. Checking if schema is applied...")
        tables = await fetch_all("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        if tables:
            print(f"   ✓ Found {len(tables)} tables:")
            for table in tables:
                print(f"     - {table['table_name']}")
        else:
            print("   ⚠ No tables found. Run migrations: supabase db push")
        
        # 4. Test insert operation (if tables exist)
        if len(tables) > 0:
            print("\n4. Testing insert operation...")
            test_person = await insert_one("people", {
                "name": "Test Person",
                "email": "test@example.com",
                "person_type": "volunteer",
                "metadata": {"test": True}
            })
            print(f"   ✓ Inserted test person with ID: {test_person['id']}")
            
            # 5. Test query operation
            print("\n5. Testing query operation...")
            found_person = await fetch_one(
                "SELECT * FROM people WHERE id = $1",
                test_person['id']
            )
            if found_person:
                print(f"   ✓ Retrieved person: {found_person['name']}")
            
            # 6. Clean up test data
            print("\n6. Cleaning up test data...")
            await execute("DELETE FROM people WHERE email = $1", "test@example.com")
            print("   ✓ Test data removed")
        
        # 7. Test seed data (if exists)
        print("\n7. Checking for seed data...")
        volunteer_count = await fetch_one(
            "SELECT COUNT(*) as count FROM people WHERE person_type = 'volunteer'"
        )
        visitor_count = await fetch_one(
            "SELECT COUNT(*) as count FROM people WHERE person_type = 'visitor'"
        )
        donor_count = await fetch_one(
            "SELECT COUNT(*) as count FROM people WHERE person_type = 'donor'"
        )
        
        if volunteer_count:
            print(f"   - Volunteers: {volunteer_count['count']}")
            print(f"   - Visitors: {visitor_count['count']}")
            print(f"   - Donors: {donor_count['count']}")
            
            if volunteer_count['count'] == 0:
                print("   ⚠ No seed data found. Run: supabase db reset")
        
        print("\n" + "=" * 60)
        print("✓ All tests passed! Database is ready to use.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you created a .env file in /orchestrator/")
        print("2. Check that DATABASE_URL is set correctly")
        print("3. Verify Supabase project is running")
        print("4. Run migrations: supabase db push")
        
    finally:
        # Close connection pool
        await close_db_pool()


if __name__ == "__main__":
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("⚠ Warning: .env file not found!")
        print("\nPlease create a .env file with your Supabase credentials.")
        print("You can copy .env.example and fill in your values:")
        print("  cp .env.example .env")
        print("\nGet your credentials from:")
        print("  https://supabase.com/dashboard → Your Project → Settings → Database")
        exit(1)
    
    # Run the test
    asyncio.run(test_connection())

