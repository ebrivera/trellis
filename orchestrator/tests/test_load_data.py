"""
Tests for load_data() function - database loading only.
For filter tests, see test_filter.py
For integration tests, see test_integration.py
Run with: python tests/test_load_data.py (from orchestrator/ directory)
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent dir to path for src imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.functions.load_data import load_data
from src.schemas import EntityType
from src.database import init_db_pool, close_db_pool


async def test_load_volunteers():
    """Test loading volunteers from people table"""
    print("\n=== Test 1: Load all volunteers ===")

    df = await load_data(EntityType.PERSON, subtype='volunteer')

    print(f"✓ Loaded {len(df)} volunteers")
    print(f"  Columns: {list(df.columns)}")

    if len(df) > 0:
        print(f"  Sample: {df.iloc[0]['name']}")
        assert df.iloc[0]['person_type'] == 'volunteer', "person_type should be 'volunteer'"

    return len(df)


async def test_load_roles():
    """Test loading roles from groups table"""
    print("\n=== Test 2: Load all roles ===")

    df = await load_data(EntityType.GROUP, subtype='role')

    print(f"✓ Loaded {len(df)} roles")

    if len(df) > 0:
        print(f"  Sample: {df.iloc[0]['name']}")
        assert df.iloc[0]['group_type'] == 'role', "group_type should be 'role'"

    return len(df)


async def test_load_gifts():
    """Test loading gifts (no subtype)"""
    print("\n=== Test 3: Load all gifts ===")

    df = await load_data(EntityType.GIFT)

    print(f"✓ Loaded {len(df)} gifts")

    if len(df) > 0:
        sample = df.iloc[0]
        print(f"  Sample: amount ${sample['amount']}, date: {sample['gift_date']}")

    return len(df)


async def test_load_initiatives():
    """Test loading initiatives from groups"""
    print("\n=== Test 4: Load all initiatives ===")

    df = await load_data(EntityType.GROUP, subtype='initiative')

    print(f"✓ Loaded {len(df)} initiatives")

    if len(df) > 0:
        sample = df.iloc[0]
        print(f"  Sample: {sample['name']} - goal: ${sample.get('goal', 0)}")
        assert sample['group_type'] == 'initiative', "group_type should be 'initiative'"

    return len(df)


async def test_load_all_people():
    """Test loading all people (no subtype filter)"""
    print("\n=== Test 5: Load all people (no subtype) ===")

    df = await load_data(EntityType.PERSON)

    print(f"✓ Loaded {len(df)} people total")

    # Count by type
    if len(df) > 0:
        type_counts = df['person_type'].value_counts()
        print(f"  Breakdown: {dict(type_counts)}")

    return len(df)


async def test_load_visitors():
    """Test loading visitors from people table"""
    print("\n=== Test 6: Load all visitors ===")

    df = await load_data(EntityType.PERSON, subtype='visitor')

    print(f"✓ Loaded {len(df)} visitors")

    if len(df) > 0:
        sample = df.iloc[0]
        print(f"  Sample: {sample['name']} visited {sample.get('visit_date')}")
        assert sample['person_type'] == 'visitor', "person_type should be 'visitor'"

    return len(df)


async def test_load_mentors():
    """Test loading mentors from people table"""
    print("\n=== Test 7: Load all mentors ===")

    df = await load_data(EntityType.PERSON, subtype='mentor')

    print(f"✓ Loaded {len(df)} mentors")

    if len(df) > 0:
        print(f"  Sample: {df.iloc[0]['name']}")
        assert df.iloc[0]['person_type'] == 'mentor', "person_type should be 'mentor'"

    return len(df)


async def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Testing load_data() function - Database loading only")
    print("=" * 60)

    # Initialize database
    print("\n1. Initializing database connection pool...")
    await init_db_pool()
    print("   ✓ Connection pool initialized\n")

    results = {}

    try:
        # Run tests
        results['volunteers'] = await test_load_volunteers()
        results['roles'] = await test_load_roles()
        results['gifts'] = await test_load_gifts()
        results['initiatives'] = await test_load_initiatives()
        results['all_people'] = await test_load_all_people()
        results['visitors'] = await test_load_visitors()
        results['mentors'] = await test_load_mentors()

        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        for test_name, count in results.items():
            print(f"  {test_name}: {count} rows")

        print("\n✓ All 7 load_data tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        print("\n2. Closing database connection pool...")
        await close_db_pool()
        print("   ✓ Connection pool closed")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
