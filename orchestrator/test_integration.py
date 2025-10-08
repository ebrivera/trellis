"""
Integration tests for load_data() + filter.py workflow.
Tests the complete two-step pipeline: Load from DB → Filter DataFrame
Run with: python test_integration.py
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent))

from src.functions.load_data import load_data
from src.functions.filter import filter_data, filter_by_time_condition
from src.schemas import EntityType, FilterCondition
from src.database import init_db_pool, close_db_pool


async def test_volunteers_with_wednesday_filter():
    """Integration: Load volunteers → filter for Wednesday availability"""
    print("\n=== Test 1: Volunteers available on Wednesday ===")

    # Step 1: Load from database
    all_volunteers = await load_data(EntityType.PERSON, subtype='volunteer')
    print(f"  Loaded {len(all_volunteers)} volunteers from DB")

    # Step 2: Filter with filter.py
    filters = [FilterCondition(field='availability_days', operator='contains', value='Wed')]
    wednesday_volunteers = filter_data(all_volunteers, filters)

    print(f"✓ Filtered to {len(wednesday_volunteers)} Wednesday volunteers")

    if len(wednesday_volunteers) > 0:
        sample = wednesday_volunteers.iloc[0]
        print(f"  Sample: {sample['name']} - {sample.get('availability_days')}")
        assert 'Wed' in sample.get('availability_days', [])

    return len(wednesday_volunteers)


async def test_roles_with_capacity():
    """Integration: Load roles → filter for capacity > 0"""
    print("\n=== Test 2: Roles with capacity > 0 ===")

    # Load all roles
    all_roles = await load_data(EntityType.GROUP, subtype='role')
    print(f"  Loaded {len(all_roles)} roles from DB")

    # Filter for capacity
    filters = [FilterCondition(field='capacity', operator='>', value='0')]
    available_roles = filter_data(all_roles, filters)

    print(f"✓ Filtered to {len(available_roles)} roles with capacity")

    if len(available_roles) > 0:
        sample = available_roles.iloc[0]
        print(f"  Sample: {sample['name']} - capacity: {sample['capacity']}")
        assert sample['capacity'] > 0

    return len(available_roles)


async def test_old_visitors_time_filter():
    """Integration: Load visitors → filter by time (>30 days ago)"""
    print("\n=== Test 3: Visitors from >30 days ago ===")

    # Load all visitors
    all_visitors = await load_data(EntityType.PERSON, subtype='visitor')
    print(f"  Loaded {len(all_visitors)} visitors from DB")

    # Filter by time
    old_visitors = filter_by_time_condition(
        all_visitors,
        time_field='visit_date',
        threshold='30 days',
        operator='>'
    )

    print(f"✓ Filtered to {len(old_visitors)} old visitors")

    if len(old_visitors) > 0:
        sample = old_visitors.iloc[0]
        print(f"  Sample: {sample['name']} visited {sample.get('visit_date')}")

    return len(old_visitors)


async def test_multiple_filters_volunteers():
    """Integration: Load volunteers → apply multiple filters"""
    print("\n=== Test 4: Volunteers with Sunday availability AND capacity > 0 ===")

    # Load all volunteers
    all_volunteers = await load_data(EntityType.PERSON, subtype='volunteer')
    print(f"  Loaded {len(all_volunteers)} volunteers from DB")

    # Apply multiple filters
    filters = [
        FilterCondition(field='availability_days', operator='contains', value='Sun'),
        FilterCondition(field='capacity', operator='>', value='0')
    ]
    filtered = filter_data(all_volunteers, filters)

    print(f"✓ Filtered to {len(filtered)} volunteers matching all criteria")

    if len(filtered) > 0:
        sample = filtered.iloc[0]
        print(f"  Sample: {sample['name']} - {sample.get('availability_days')}, capacity: {sample.get('capacity')}")
        assert 'Sun' in sample.get('availability_days', [])
        assert sample.get('capacity', 0) > 0

    return len(filtered)


async def test_all_people_then_filter_by_type():
    """Integration: Load all people → filter by person_type"""
    print("\n=== Test 5: Load all people → filter to mentors ===")

    # Load all people (no subtype)
    all_people = await load_data(EntityType.PERSON)
    print(f"  Loaded {len(all_people)} people from DB")

    # Filter to just mentors using filter.py
    filters = [FilterCondition(field='person_type', operator='=', value='mentor')]
    mentors = filter_data(all_people, filters)

    print(f"✓ Filtered to {len(mentors)} mentors")

    if len(mentors) > 0:
        assert all(mentors['person_type'] == 'mentor')

    return len(mentors)


async def run_all_tests():
    """Run all integration tests"""
    print("=" * 60)
    print("Integration Tests: load_data() + filter.py")
    print("=" * 60)

    # Initialize database
    print("\n1. Initializing database connection pool...")
    await init_db_pool()
    print("   ✓ Connection pool initialized\n")

    results = {}

    try:
        # Run integration tests
        results['wednesday_volunteers'] = await test_volunteers_with_wednesday_filter()
        results['roles_with_capacity'] = await test_roles_with_capacity()
        results['old_visitors'] = await test_old_visitors_time_filter()
        results['multiple_filters'] = await test_multiple_filters_volunteers()
        results['all_people_to_mentors'] = await test_all_people_then_filter_by_type()

        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        for test_name, count in results.items():
            print(f"  {test_name}: {count} rows")

        print("\n✓ All 5 integration tests passed!")
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
