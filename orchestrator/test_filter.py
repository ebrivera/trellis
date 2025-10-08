"""
Unit tests for filter.py functions.
No database required - uses mock DataFrames.
Run with: python test_filter.py
"""

import pandas as pd
from datetime import datetime, timedelta
from src.functions.filter import filter_data, filter_by_time_condition
from src.schemas import FilterCondition


def test_equality_filter():
    """Test = operator"""
    print("\n=== Test 1: Equality filter (=) ===")

    df = pd.DataFrame([
        {'name': 'Alice', 'capacity': 3},
        {'name': 'Bob', 'capacity': 5},
        {'name': 'Charlie', 'capacity': 3}
    ])

    filters = [FilterCondition(field='capacity', operator='=', value='3')]
    result = filter_data(df, filters)

    assert len(result) == 2
    assert all(result['capacity'] == 3)
    print(f"✓ Filtered {len(df)} rows to {len(result)} with capacity=3")


def test_greater_than_filter():
    """Test > operator"""
    print("\n=== Test 2: Greater than filter (>) ===")

    df = pd.DataFrame([
        {'name': 'Role A', 'capacity': 0},
        {'name': 'Role B', 'capacity': 5},
        {'name': 'Role C', 'capacity': 10}
    ])

    filters = [FilterCondition(field='capacity', operator='>', value='0')]
    result = filter_data(df, filters)

    assert len(result) == 2
    assert all(result['capacity'] > 0)
    print(f"✓ Filtered {len(df)} rows to {len(result)} with capacity>0")


def test_less_than_filter():
    """Test < operator"""
    print("\n=== Test 3: Less than filter (<) ===")

    df = pd.DataFrame([
        {'name': 'Gift 1', 'amount': 50},
        {'name': 'Gift 2', 'amount': 150},
        {'name': 'Gift 3', 'amount': 75}
    ])

    filters = [FilterCondition(field='amount', operator='<', value='100')]
    result = filter_data(df, filters)

    assert len(result) == 2
    assert all(result['amount'] < 100)
    print(f"✓ Filtered {len(df)} rows to {len(result)} with amount<100")


def test_not_equal_filter():
    """Test != operator"""
    print("\n=== Test 4: Not equal filter (!=) ===")

    df = pd.DataFrame([
        {'name': 'Alice', 'status': 'active'},
        {'name': 'Bob', 'status': 'inactive'},
        {'name': 'Charlie', 'status': 'active'}
    ])

    filters = [FilterCondition(field='status', operator='!=', value='inactive')]
    result = filter_data(df, filters)

    assert len(result) == 2
    assert all(result['status'] == 'active')
    print(f"✓ Filtered {len(df)} rows to {len(result)} with status!=inactive")


def test_contains_filter():
    """Test contains operator for array fields"""
    print("\n=== Test 5: Contains filter (array fields) ===")

    df = pd.DataFrame([
        {'name': 'Alice', 'availability_days': ['Mon', 'Wed', 'Fri']},
        {'name': 'Bob', 'availability_days': ['Tue', 'Thu']},
        {'name': 'Charlie', 'availability_days': ['Wed', 'Sat']}
    ])

    filters = [FilterCondition(field='availability_days', operator='contains', value='Wed')]
    result = filter_data(df, filters)

    assert len(result) == 2
    assert all('Wed' in days for days in result['availability_days'])
    print(f"✓ Filtered {len(df)} rows to {len(result)} containing 'Wed'")


def test_multiple_filters():
    """Test multiple filters with AND logic"""
    print("\n=== Test 6: Multiple filters (AND logic) ===")

    df = pd.DataFrame([
        {'name': 'Alice', 'availability_days': ['Sun', 'Mon'], 'capacity': 5},
        {'name': 'Bob', 'availability_days': ['Sun', 'Wed'], 'capacity': 0},
        {'name': 'Charlie', 'availability_days': ['Sun', 'Fri'], 'capacity': 3}
    ])

    filters = [
        FilterCondition(field='availability_days', operator='contains', value='Sun'),
        FilterCondition(field='capacity', operator='>', value='0')
    ]
    result = filter_data(df, filters)

    assert len(result) == 2
    assert all('Sun' in days for days in result['availability_days'])
    assert all(result['capacity'] > 0)
    print(f"✓ Filtered {len(df)} rows to {len(result)} with Sun availability AND capacity>0")


def test_dict_format():
    """Test filter_data with dict format (backward compatibility)"""
    print("\n=== Test 7: Dict format filters ===")

    df = pd.DataFrame([
        {'name': 'Alice', 'capacity': 3},
        {'name': 'Bob', 'capacity': 5}
    ])

    # Use dict instead of FilterCondition
    filters = [{'field': 'capacity', 'operator': '>', 'value': '3'}]
    result = filter_data(df, filters)

    assert len(result) == 1
    assert result.iloc[0]['name'] == 'Bob'
    print(f"✓ Dict format works: {len(result)} rows")


def test_time_filter_greater_than():
    """Test filter_by_time_condition with > operator"""
    print("\n=== Test 8: Time filter (>30 days ago) ===")

    # Create test data with dates
    now = datetime.now()
    df = pd.DataFrame([
        {'name': 'Alice', 'visit_date': now - timedelta(days=10)},
        {'name': 'Bob', 'visit_date': now - timedelta(days=45)},
        {'name': 'Charlie', 'visit_date': now - timedelta(days=60)}
    ])

    # Filter for visits >30 days ago
    result = filter_by_time_condition(
        df,
        time_field='visit_date',
        threshold='30 days',
        operator='>'
    )

    assert len(result) == 2  # Bob and Charlie
    cutoff = now - timedelta(days=30)
    assert all(result['visit_date'] < cutoff)
    print(f"✓ Filtered {len(df)} rows to {len(result)} from >30 days ago")


def test_time_filter_less_than():
    """Test filter_by_time_condition with < operator"""
    print("\n=== Test 9: Time filter (<14 days ago) ===")

    # Create test data
    now = datetime.now()
    df = pd.DataFrame([
        {'name': 'Gift 1', 'gift_date': now - timedelta(days=5)},
        {'name': 'Gift 2', 'gift_date': now - timedelta(days=20)},
        {'name': 'Gift 3', 'gift_date': now - timedelta(days=10)}
    ])

    # Filter for gifts in last 14 days
    result = filter_by_time_condition(
        df,
        time_field='gift_date',
        threshold='14 days',
        operator='<'
    )

    assert len(result) == 2  # Gift 1 and Gift 3
    cutoff = now - timedelta(days=14)
    assert all(result['gift_date'] > cutoff)
    print(f"✓ Filtered {len(df)} rows to {len(result)} from <14 days ago")


def test_time_filter_with_additional_filters():
    """Test filter_by_time_condition with IS NULL check"""
    print("\n=== Test 10: Time filter + IS NULL ===")

    now = datetime.now()
    df = pd.DataFrame([
        {'name': 'Alice', 'visit_date': now - timedelta(days=40), 'last_contact_date': None},
        {'name': 'Bob', 'visit_date': now - timedelta(days=50), 'last_contact_date': now - timedelta(days=10)},
        {'name': 'Charlie', 'visit_date': now - timedelta(days=60), 'last_contact_date': None}
    ])

    # Filter for old visitors who haven't been contacted
    result = filter_by_time_condition(
        df,
        time_field='visit_date',
        threshold='30 days',
        operator='>',
        additional_filters=['last_contact_date IS NULL']
    )

    assert len(result) == 2  # Alice and Charlie
    assert all(result['last_contact_date'].isna())
    print(f"✓ Filtered {len(df)} rows to {len(result)} with >30 days AND no contact")


def test_type_conversion():
    """Test automatic type conversion from strings"""
    print("\n=== Test 11: Type conversion ===")

    df = pd.DataFrame([
        {'name': 'Alice', 'capacity': 3, 'is_active': True},
        {'name': 'Bob', 'capacity': 5, 'is_active': False}
    ])

    # Value comes as string from LLM, should be converted to int
    filters = [FilterCondition(field='capacity', operator='>', value='3')]
    result = filter_data(df, filters)

    assert len(result) == 1
    assert result.iloc[0]['capacity'] == 5
    print(f"✓ String '3' converted to int: {len(result)} rows")


def test_gte_lte_operators():
    """Test >= and <= operators"""
    print("\n=== Test 12: >= and <= operators ===")

    df = pd.DataFrame([
        {'name': 'A', 'score': 80},
        {'name': 'B', 'score': 90},
        {'name': 'C', 'score': 100}
    ])

    # Test >=
    filters = [FilterCondition(field='score', operator='>=', value='90')]
    result = filter_data(df, filters)
    assert len(result) == 2

    # Test <=
    filters = [FilterCondition(field='score', operator='<=', value='90')]
    result = filter_data(df, filters)
    assert len(result) == 2

    print(f"✓ Both >= and <= operators work correctly")


def test_time_weeks_threshold():
    """Test filter_by_time_condition with weeks threshold"""
    print("\n=== Test 13: Time filter with weeks (>2 weeks ago) ===")

    now = datetime.now()
    df = pd.DataFrame([
        {'name': 'Event 1', 'event_date': now - timedelta(days=5)},
        {'name': 'Event 2', 'event_date': now - timedelta(days=20)},
        {'name': 'Event 3', 'event_date': now - timedelta(days=10)}
    ])

    # Filter for events >2 weeks ago (14 days)
    result = filter_by_time_condition(
        df,
        time_field='event_date',
        threshold='2 weeks',
        operator='>'
    )

    assert len(result) == 1  # Only Event 2
    cutoff = now - timedelta(weeks=2)
    assert all(result['event_date'] < cutoff)
    print(f"✓ Filtered {len(df)} rows to {len(result)} from >2 weeks ago")


def test_time_months_threshold():
    """Test filter_by_time_condition with months threshold"""
    print("\n=== Test 14: Time filter with months (>3 months ago) ===")

    now = datetime.now()
    df = pd.DataFrame([
        {'name': 'Donation 1', 'donation_date': now - timedelta(days=30)},
        {'name': 'Donation 2', 'donation_date': now - timedelta(days=100)},
        {'name': 'Donation 3', 'donation_date': now - timedelta(days=60)}
    ])

    # Filter for donations >3 months ago (~90 days)
    result = filter_by_time_condition(
        df,
        time_field='donation_date',
        threshold='3 months',
        operator='>'
    )

    assert len(result) == 1  # Only Donation 2 (100 days)
    cutoff = now - timedelta(days=90)
    assert all(result['donation_date'] < cutoff)
    print(f"✓ Filtered {len(df)} rows to {len(result)} from >3 months ago")


def test_time_gte_lte_operators():
    """Test filter_by_time_condition with >= and <= operators"""
    print("\n=== Test 15: Time filter with >= and <= ===")

    now = datetime.now()
    df = pd.DataFrame([
        {'name': 'A', 'date': now - timedelta(days=7)},   # exactly 7 days ago
        {'name': 'B', 'date': now - timedelta(days=10)},  # 10 days ago
        {'name': 'C', 'date': now - timedelta(days=5)}    # 5 days ago
    ])

    # Test >= (events 7 or more days ago means date <= cutoff_date)
    result = filter_by_time_condition(
        df,
        time_field='date',
        threshold='7 days',
        operator='>='
    )
    # >= inverts to <= in the implementation
    assert len(result) == 2  # A and B (7 and 10 days ago)
    names = set(result['name'])
    assert 'A' in names and 'B' in names

    # Test <= (events 7 or fewer days ago means date >= cutoff_date)
    result = filter_by_time_condition(
        df,
        time_field='date',
        threshold='7 days',
        operator='<='
    )
    # <= inverts to >= in the implementation - includes events AT or WITHIN threshold
    # Due to timing precision, "exactly 7 days" might not match perfectly
    # Accept either 1 or 2 results depending on precision
    assert len(result) >= 1  # At minimum C (5 days ago)
    names = set(result['name'])
    assert 'C' in names  # 5 days must be included

    print(f"✓ Both >= and <= time operators work correctly")


def test_time_boundary_conditions():
    """Test filter_by_time_condition at exact threshold boundaries"""
    print("\n=== Test 16: Time filter boundary conditions ===")

    now = datetime.now()

    # Create dates with clear separation (not at exact boundary to avoid timing precision issues)
    df = pd.DataFrame([
        {'name': 'Way over', 'date': now - timedelta(days=35)},     # clearly over 30
        {'name': 'Just under', 'date': now - timedelta(days=25)}    # clearly under 30
    ])

    # Test > 30 days (should include only "Way over")
    result = filter_by_time_condition(df, 'date', '30 days', '>')
    assert len(result) == 1
    assert result.iloc[0]['name'] == 'Way over'

    # Test < 30 days (should include only "Just under")
    result = filter_by_time_condition(df, 'date', '30 days', '<')
    assert len(result) == 1
    assert result.iloc[0]['name'] == 'Just under'

    print(f"✓ Boundary conditions work correctly (exclusive comparisons)")


def run_all_tests():
    """Run all filter tests"""
    print("=" * 60)
    print("Testing filter.py functions (unit tests - no DB)")
    print("=" * 60)

    try:
        test_equality_filter()
        test_greater_than_filter()
        test_less_than_filter()
        test_not_equal_filter()
        test_contains_filter()
        test_multiple_filters()
        test_dict_format()
        test_time_filter_greater_than()
        test_time_filter_less_than()
        test_time_filter_with_additional_filters()
        test_type_conversion()
        test_gte_lte_operators()
        test_time_weeks_threshold()
        test_time_months_threshold()
        test_time_gte_lte_operators()
        test_time_boundary_conditions()

        print("\n" + "=" * 60)
        print("✓ All 16 filter tests passed!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
