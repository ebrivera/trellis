"""
Unit tests for calculate_metrics.py functions.
No database required - uses mock DataFrames.
Run with: python test_calculate_metrics.py
"""

import pandas as pd
import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent))

from src.functions.calculate_metrics import calculate_metrics
from src.templates.analysis import MetricFormula


def test_sum_basic():
    """Test basic SUM aggregation"""
    print("\n=== Test 1: Basic SUM ===")

    df = pd.DataFrame([
        {'amount': 100},
        {'amount': 200},
        {'amount': 300}
    ])

    formulas = [MetricFormula(name='total', formula='SUM(amount)')]
    results = calculate_metrics(formulas, df)

    assert results['total'] == 600.0
    print(f"✓ SUM(amount) = {results['total']}")


def test_avg_basic():
    """Test basic AVG aggregation"""
    print("\n=== Test 2: Basic AVG ===")

    df = pd.DataFrame([
        {'amount': 100},
        {'amount': 200},
        {'amount': 300}
    ])

    formulas = [MetricFormula(name='average', formula='AVG(amount)')]
    results = calculate_metrics(formulas, df)

    assert results['average'] == 200.0
    print(f"✓ AVG(amount) = {results['average']}")


def test_count_star():
    """Test COUNT(*) aggregation"""
    print("\n=== Test 3: COUNT(*) ===")

    df = pd.DataFrame([
        {'name': 'Alice'},
        {'name': 'Bob'},
        {'name': 'Charlie'}
    ])

    formulas = [MetricFormula(name='total_count', formula='COUNT(*)')]
    results = calculate_metrics(formulas, df)

    assert results['total_count'] == 3
    print(f"✓ COUNT(*) = {results['total_count']}")


def test_count_distinct():
    """Test COUNT DISTINCT aggregation"""
    print("\n=== Test 4: COUNT DISTINCT ===")

    df = pd.DataFrame([
        {'donor': 'Alice', 'amount': 100},
        {'donor': 'Bob', 'amount': 200},
        {'donor': 'Alice', 'amount': 150}
    ])

    formulas = [MetricFormula(name='unique_donors', formula='COUNT(DISTINCT donor)')]
    results = calculate_metrics(formulas, df)

    assert results['unique_donors'] == 2  # Alice and Bob
    print(f"✓ COUNT(DISTINCT donor) = {results['unique_donors']}")


def test_min_max():
    """Test MIN and MAX aggregations"""
    print("\n=== Test 5: MIN and MAX ===")

    df = pd.DataFrame([
        {'amount': 50},
        {'amount': 200},
        {'amount': 25}
    ])

    formulas = [
        MetricFormula(name='min_gift', formula='MIN(amount)'),
        MetricFormula(name='max_gift', formula='MAX(amount)')
    ]
    results = calculate_metrics(formulas, df)

    assert results['min_gift'] == 25.0
    assert results['max_gift'] == 200.0
    print(f"✓ MIN = {results['min_gift']}, MAX = {results['max_gift']}")


def test_group_by():
    """Test aggregation with GROUP BY"""
    print("\n=== Test 6: GROUP BY ===")

    df = pd.DataFrame([
        {'initiative': 'Building Fund', 'amount': 100},
        {'initiative': 'Building Fund', 'amount': 200},
        {'initiative': 'Youth Program', 'amount': 150},
        {'initiative': 'Youth Program', 'amount': 250}
    ])

    formulas = [
        MetricFormula(
            name='total_by_initiative',
            formula='SUM(amount)',
            group_by='initiative'
        )
    ]
    results = calculate_metrics(formulas, df)

    assert results['total_by_initiative']['Building Fund'] == 300.0
    assert results['total_by_initiative']['Youth Program'] == 400.0
    print(f"✓ Grouped results: {results['total_by_initiative']}")


def test_group_by_in_formula():
    """Test GROUP BY specified in formula string"""
    print("\n=== Test 7: GROUP BY in formula ===")

    df = pd.DataFrame([
        {'initiative': 'Fund A', 'amount': 100},
        {'initiative': 'Fund A', 'amount': 200},
        {'initiative': 'Fund B', 'amount': 300}
    ])

    formulas = [
        MetricFormula(
            name='by_fund',
            formula='SUM(amount) GROUP BY initiative'
        )
    ]
    results = calculate_metrics(formulas, df)

    assert results['by_fund']['Fund A'] == 300.0
    assert results['by_fund']['Fund B'] == 300.0
    print(f"✓ GROUP BY from formula: {results['by_fund']}")


def test_calculated_metric():
    """Test calculated metric referencing other metrics"""
    print("\n=== Test 8: Calculated metric ===")

    df = pd.DataFrame([
        {'amount': 1000},
        {'amount': 2000},
        {'amount': 3000}
    ])

    formulas = [
        MetricFormula(name='total_raised', formula='SUM(amount)'),
        MetricFormula(name='donor_count', formula='COUNT(*)'),
        MetricFormula(name='avg_gift', formula='total_raised / donor_count')
    ]
    results = calculate_metrics(formulas, df)

    assert results['total_raised'] == 6000.0
    assert results['donor_count'] == 3
    assert results['avg_gift'] == 2000.0
    print(f"✓ Calculated: {results['avg_gift']} = {results['total_raised']} / {results['donor_count']}")


def test_format_currency():
    """Test currency formatting"""
    print("\n=== Test 9: Currency formatting ===")

    df = pd.DataFrame([
        {'amount': 1234.56},
        {'amount': 2000.00}
    ])

    formulas = [
        MetricFormula(name='total', formula='SUM(amount)', format='currency')
    ]
    results = calculate_metrics(formulas, df)

    assert results['total'] == '$3,234.56'
    print(f"✓ Formatted: {results['total']}")


def test_format_percent():
    """Test percent formatting"""
    print("\n=== Test 10: Percent formatting ===")

    df = pd.DataFrame([
        {'rate': 0.75}
    ])

    formulas = [
        MetricFormula(name='completion_rate', formula='AVG(rate)', format='percent')
    ]
    results = calculate_metrics(formulas, df)

    assert results['completion_rate'] == '75.0%'
    print(f"✓ Formatted: {results['completion_rate']}")


def test_format_number():
    """Test number formatting"""
    print("\n=== Test 11: Number formatting ===")

    df = pd.DataFrame([
        {'count': 1000},
        {'count': 2500}
    ])

    formulas = [
        MetricFormula(name='total_count', formula='SUM(count)', format='number')
    ]
    results = calculate_metrics(formulas, df)

    assert results['total_count'] == '3,500'
    print(f"✓ Formatted: {results['total_count']}")


def test_case_insensitive():
    """Test case-insensitive formula parsing"""
    print("\n=== Test 12: Case insensitive ===")

    df = pd.DataFrame([
        {'amount': 100},
        {'amount': 200}
    ])

    formulas = [
        MetricFormula(name='test1', formula='sum(amount)'),
        MetricFormula(name='test2', formula='SUM(amount)'),
        MetricFormula(name='test3', formula='Sum(amount)')
    ]
    results = calculate_metrics(formulas, df)

    assert results['test1'] == 300.0
    assert results['test2'] == 300.0
    assert results['test3'] == 300.0
    print("✓ Case insensitive formulas work")


def test_whitespace_handling():
    """Test handling of extra whitespace"""
    print("\n=== Test 13: Whitespace handling ===")

    df = pd.DataFrame([
        {'amount': 100}
    ])

    formulas = [
        MetricFormula(name='test1', formula='  SUM(amount)  '),
        MetricFormula(name='test2', formula='SUM( amount )'),
        MetricFormula(name='test3', formula='  SUM  (  amount  )  ')
    ]
    results = calculate_metrics(formulas, df)

    assert all(results[f'test{i}'] == 100.0 for i in [1, 2, 3])
    print("✓ Whitespace handled correctly")


def test_error_handling_missing_column():
    """Test error handling for missing column"""
    print("\n=== Test 14: Error - missing column ===")

    df = pd.DataFrame([
        {'amount': 100}
    ])

    formulas = [
        MetricFormula(name='bad_metric', formula='SUM(nonexistent_column)')
    ]
    results = calculate_metrics(formulas, df)

    assert 'error' in results['bad_metric']
    assert 'nonexistent_column' in results['bad_metric']['error']
    print(f"✓ Caught error: {results['bad_metric']['error']}")


def test_error_handling_invalid_formula():
    """Test error handling for invalid formula"""
    print("\n=== Test 15: Error - invalid formula ===")

    df = pd.DataFrame([
        {'amount': 100}
    ])

    formulas = [
        MetricFormula(name='bad_formula', formula='INVALID SYNTAX')
    ]
    results = calculate_metrics(formulas, df)

    assert 'error' in results['bad_formula']
    print(f"✓ Caught error: {results['bad_formula']['error']}")


def test_multiple_metrics():
    """Test calculating multiple metrics in one call"""
    print("\n=== Test 16: Multiple metrics ===")

    df = pd.DataFrame([
        {'donor': 'Alice', 'amount': 100},
        {'donor': 'Bob', 'amount': 200},
        {'donor': 'Alice', 'amount': 150}
    ])

    formulas = [
        MetricFormula(name='total_raised', formula='SUM(amount)'),
        MetricFormula(name='gift_count', formula='COUNT(*)'),
        MetricFormula(name='unique_donors', formula='COUNT(DISTINCT donor)'),
        MetricFormula(name='avg_gift', formula='AVG(amount)'),
        MetricFormula(name='min_gift', formula='MIN(amount)'),
        MetricFormula(name='max_gift', formula='MAX(amount)')
    ]
    results = calculate_metrics(formulas, df)

    assert results['total_raised'] == 450.0
    assert results['gift_count'] == 3
    assert results['unique_donors'] == 2
    assert results['avg_gift'] == 150.0
    assert results['min_gift'] == 100.0
    assert results['max_gift'] == 200.0
    print(f"✓ All 6 metrics calculated correctly")


def test_grouped_with_count_distinct():
    """Test GROUP BY with COUNT DISTINCT"""
    print("\n=== Test 17: GROUP BY + COUNT DISTINCT ===")

    df = pd.DataFrame([
        {'initiative': 'Fund A', 'donor': 'Alice'},
        {'initiative': 'Fund A', 'donor': 'Bob'},
        {'initiative': 'Fund A', 'donor': 'Alice'},  # Duplicate
        {'initiative': 'Fund B', 'donor': 'Charlie'},
        {'initiative': 'Fund B', 'donor': 'Charlie'}  # Duplicate
    ])

    formulas = [
        MetricFormula(
            name='unique_donors_per_fund',
            formula='COUNT(DISTINCT donor)',
            group_by='initiative'
        )
    ]
    results = calculate_metrics(formulas, df)

    assert results['unique_donors_per_fund']['Fund A'] == 2
    assert results['unique_donors_per_fund']['Fund B'] == 1
    print(f"✓ Grouped COUNT DISTINCT: {results['unique_donors_per_fund']}")


def test_complex_calculated_metric():
    """Test calculated metric with multiple operations"""
    print("\n=== Test 18: Complex calculated metric ===")

    df = pd.DataFrame([
        {'goal': 10000, 'amount': 7500}
    ])

    formulas = [
        MetricFormula(name='total_raised', formula='SUM(amount)'),
        MetricFormula(name='goal', formula='SUM(goal)'),
        MetricFormula(name='progress', formula='total_raised / goal')
    ]
    results = calculate_metrics(formulas, df)

    assert results['progress'] == 0.75
    print(f"✓ Progress: {results['progress']} ({results['total_raised']} / {results['goal']})")


def test_empty_dataframe():
    """Test handling of empty DataFrame"""
    print("\n=== Test 19: Empty DataFrame ===")

    df = pd.DataFrame(columns=['amount'])

    formulas = [
        MetricFormula(name='total', formula='SUM(amount)'),
        MetricFormula(name='count', formula='COUNT(*)')
    ]
    results = calculate_metrics(formulas, df)

    # SUM of empty should be 0, COUNT should be 0
    assert results['total'] == 0.0
    assert results['count'] == 0
    print(f"✓ Empty DataFrame handled: total={results['total']}, count={results['count']}")


def test_format_grouped_results():
    """Test formatting of grouped results"""
    print("\n=== Test 20: Format grouped results ===")

    df = pd.DataFrame([
        {'fund': 'A', 'amount': 1234.56},
        {'fund': 'B', 'amount': 5678.90}
    ])

    formulas = [
        MetricFormula(
            name='total_by_fund',
            formula='SUM(amount)',
            group_by='fund',
            format='currency'
        )
    ]
    results = calculate_metrics(formulas, df)

    assert results['total_by_fund']['A'] == '$1,234.56'
    assert results['total_by_fund']['B'] == '$5,678.90'
    print(f"✓ Formatted grouped: {results['total_by_fund']}")


def run_all_tests():
    """Run all calculate_metrics tests"""
    print("=" * 60)
    print("Testing calculate_metrics.py functions (unit tests - no DB)")
    print("=" * 60)

    try:
        test_sum_basic()
        test_avg_basic()
        test_count_star()
        test_count_distinct()
        test_min_max()
        test_group_by()
        test_group_by_in_formula()
        test_calculated_metric()
        test_format_currency()
        test_format_percent()
        test_format_number()
        test_case_insensitive()
        test_whitespace_handling()
        test_error_handling_missing_column()
        test_error_handling_invalid_formula()
        test_multiple_metrics()
        test_grouped_with_count_distinct()
        test_complex_calculated_metric()
        test_empty_dataframe()
        test_format_grouped_results()

        print("\n" + "=" * 60)
        print("✓ All 20 calculate_metrics tests passed!")
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
