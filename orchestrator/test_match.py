"""
Unit tests for match.py functions.
No database required - uses mock DataFrames.
Run with: python test_match.py
"""

import pandas as pd
import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent))

from src.functions.match import (
    match,
    calculate_match_score,
    _score_single_field,
    _jaccard_similarity,
    _calculate_weighted_score
)
from src.schemas import MatchStrategy
from src.templates.matching import MatchFields, FieldWeight, MatchConstraints


def test_jaccard_similarity():
    """Test Jaccard similarity calculation"""
    print("\n=== Test 1: Jaccard similarity ===")

    # Perfect overlap
    assert _jaccard_similarity(['a', 'b', 'c'], ['a', 'b', 'c']) == 1.0

    # Partial overlap
    score = _jaccard_similarity(['a', 'b'], ['b', 'c'])
    assert 0.33 <= score <= 0.34  # 1/3

    # No overlap
    assert _jaccard_similarity(['a'], ['b']) == 0.0

    # Empty lists
    assert _jaccard_similarity([], ['a']) == 0.0
    assert _jaccard_similarity(['a'], []) == 0.0

    print("✓ Jaccard similarity works correctly")


def test_score_single_field_arrays():
    """Test field scoring for array fields"""
    print("\n=== Test 2: Score array fields ===")

    source = pd.Series({'interests': ['music', 'youth', 'teaching']})
    target = pd.Series({'interests': ['music', 'youth']})

    score = _score_single_field(source, target, 'interests')
    assert 0.66 <= score <= 0.67  # 2/3

    print(f"✓ Array field scoring: {score:.2f}")


def test_score_single_field_strings():
    """Test field scoring for string fields"""
    print("\n=== Test 3: Score string fields ===")

    # Exact match
    source = pd.Series({'name': 'Alice'})
    target = pd.Series({'name': 'alice'})  # Case insensitive
    assert _score_single_field(source, target, 'name') == 1.0

    # Substring match
    source = pd.Series({'skill': 'teaching'})
    target = pd.Series({'skill': 'teaching experience'})
    assert _score_single_field(source, target, 'skill') == 0.5

    # No match
    source = pd.Series({'skill': 'music'})
    target = pd.Series({'skill': 'sports'})
    assert _score_single_field(source, target, 'skill') == 0.0

    print("✓ String field scoring works correctly")


def test_score_single_field_numbers():
    """Test field scoring for numeric fields"""
    print("\n=== Test 4: Score numeric fields ===")

    # Identical numbers
    source = pd.Series({'age': 25})
    target = pd.Series({'age': 25})
    assert _score_single_field(source, target, 'age') == 1.0

    # Close numbers (within 10%)
    source = pd.Series({'capacity': 100})
    target = pd.Series({'capacity': 95})
    score = _score_single_field(source, target, 'capacity')
    assert score > 0.9  # Very similar

    # Different numbers
    source = pd.Series({'capacity': 10})
    target = pd.Series({'capacity': 100})
    score = _score_single_field(source, target, 'capacity')
    assert score < 0.5  # Very different

    print("✓ Numeric field scoring works correctly")


def test_weighted_score_single_field():
    """Test weighted scoring with single field"""
    print("\n=== Test 5: Weighted score (single field) ===")

    source = pd.Series({'interests': ['music', 'youth']})
    target = pd.Series({'interests': ['music', 'worship']})

    match_fields = MatchFields(
        score_on=['interests'],
        weights=[FieldWeight(field='interests', weight=1.0)]
    )

    score = _calculate_weighted_score(source, target, match_fields)
    assert 0.33 <= score <= 0.34  # 1/3 overlap

    print(f"✓ Single field weighted score: {score:.2f}")


def test_weighted_score_multiple_fields():
    """Test weighted scoring with multiple fields"""
    print("\n=== Test 6: Weighted score (multiple fields) ===")

    source = pd.Series({
        'interests': ['music', 'youth'],  # 0.33 score
        'zip': '12345'                    # 1.0 score (exact match)
    })
    target = pd.Series({
        'interests': ['music', 'worship'],
        'zip': '12345'
    })

    match_fields = MatchFields(
        score_on=['interests', 'zip'],
        weights=[
            FieldWeight(field='interests', weight=0.6),
            FieldWeight(field='zip', weight=0.4)
        ]
    )

    score = _calculate_weighted_score(source, target, match_fields)
    # 0.33 * 0.6 + 1.0 * 0.4 = 0.198 + 0.4 = 0.598
    assert 0.59 <= score <= 0.60

    print(f"✓ Multi-field weighted score: {score:.2f}")


def test_match_interest_overlap():
    """Test matching with interest_overlap strategy"""
    print("\n=== Test 7: Match with interest_overlap strategy ===")

    # Create test data
    volunteers = pd.DataFrame([
        {'id': 'v1', 'name': 'Alice', 'interests': ['music', 'youth']},
        {'id': 'v2', 'name': 'Bob', 'interests': ['teaching', 'youth']},
        {'id': 'v3', 'name': 'Charlie', 'interests': ['music', 'worship']}
    ])

    roles = pd.DataFrame([
        {'id': 'r1', 'name': 'Youth Leader', 'interests': ['youth', 'teaching'], 'capacity': 2},
        {'id': 'r2', 'name': 'Worship Team', 'interests': ['music', 'worship'], 'capacity': 1}
    ])

    match_fields = MatchFields(
        score_on=['interests'],
        weights=[FieldWeight(field='interests', weight=1.0)]
    )

    constraints = MatchConstraints(
        max_per_target='capacity',
        min_score_threshold=0.3
    )

    assignments = match(
        volunteers,
        roles,
        MatchStrategy.INTEREST_OVERLAP,
        match_fields,
        constraints
    )

    # Verify assignments
    assert len(assignments) == 3  # All volunteers matched
    print(f"✓ Created {len(assignments)} assignments")

    # Check specific matches
    alice = next(a for a in assignments if a['source_id'] == 'v1')
    bob = next(a for a in assignments if a['source_id'] == 'v2')
    charlie = next(a for a in assignments if a['source_id'] == 'v3')

    print(f"  Alice → {alice['target_name']} (score: {alice['match_score']})")
    print(f"  Bob → {bob['target_name']} (score: {bob['match_score']})")
    print(f"  Charlie → {charlie['target_name']} (score: {charlie['match_score']})")

    # Bob should match Youth Leader (perfect match: 2/2 = 1.0)
    assert bob['target_id'] == 'r1'
    assert bob['match_score'] == 1.0

    # Charlie should match Worship Team (perfect match: 2/2 = 1.0)
    assert charlie['target_id'] == 'r2'
    assert charlie['match_score'] == 1.0


def test_match_capacity_constraint():
    """Test that capacity constraints are respected"""
    print("\n=== Test 8: Match respects capacity constraints ===")

    # 3 volunteers, 1 role with capacity=2
    volunteers = pd.DataFrame([
        {'id': 'v1', 'name': 'Alice', 'interests': ['music']},
        {'id': 'v2', 'name': 'Bob', 'interests': ['music']},
        {'id': 'v3', 'name': 'Charlie', 'interests': ['music']}
    ])

    roles = pd.DataFrame([
        {'id': 'r1', 'name': 'Role A', 'interests': ['music'], 'capacity': 2}
    ])

    match_fields = MatchFields(
        score_on=['interests'],
        weights=[FieldWeight(field='interests', weight=1.0)]
    )

    constraints = MatchConstraints(max_per_target='capacity')

    assignments = match(volunteers, roles, MatchStrategy.INTEREST_OVERLAP, match_fields, constraints)

    # Only 2 should be assigned (capacity limit)
    assert len(assignments) == 2
    print(f"✓ Correctly assigned {len(assignments)}/3 volunteers (capacity=2)")


def test_match_min_threshold():
    """Test minimum score threshold filtering"""
    print("\n=== Test 9: Match filters by min threshold ===")

    volunteers = pd.DataFrame([
        {'id': 'v1', 'name': 'Alice', 'interests': ['music', 'youth', 'worship']},  # Better match (2/3 = 0.67)
        {'id': 'v2', 'name': 'Bob', 'interests': ['sports']}  # Poor match (0.0)
    ])

    roles = pd.DataFrame([
        {'id': 'r1', 'name': 'Music Role', 'interests': ['music', 'worship'], 'capacity': 10}
    ])

    match_fields = MatchFields(
        score_on=['interests'],
        weights=[FieldWeight(field='interests', weight=1.0)]
    )

    # Set threshold at 0.5 (only good matches)
    constraints = MatchConstraints(
        max_per_target='capacity',
        min_score_threshold=0.5
    )

    assignments = match(volunteers, roles, MatchStrategy.INTEREST_OVERLAP, match_fields, constraints)

    # Only Alice should match (score=0.67 > 0.5), Bob filtered out (score=0.0)
    assert len(assignments) == 1
    assert assignments[0]['source_id'] == 'v1'
    print(f"✓ Only 1/2 volunteers matched (threshold=0.5)")


def test_match_capacity_balanced_strategy():
    """Test capacity_balanced strategy adds capacity bonus"""
    print("\n=== Test 10: Capacity balanced strategy ===")

    # Use partial match so base score < 1.0, allowing bonus to show
    source = pd.Series({'interests': ['music', 'youth']})

    # Two targets with partial overlap but different capacity
    target1 = pd.Series({'interests': ['music'], 'capacity': 5})
    target2 = pd.Series({'interests': ['music'], 'capacity': 50})

    match_fields = MatchFields(
        score_on=['interests'],
        weights=[FieldWeight(field='interests', weight=1.0)]
    )

    constraints = MatchConstraints()

    score1 = calculate_match_score(source, target1, MatchStrategy.CAPACITY_BALANCED, match_fields, constraints)
    score2 = calculate_match_score(source, target2, MatchStrategy.CAPACITY_BALANCED, match_fields, constraints)

    # Target with higher capacity should have higher score (base=0.5, bonus differs)
    assert score2 > score1
    print(f"✓ Capacity bonus: target1(cap=5)={score1:.2f}, target2(cap=50)={score2:.2f}")


def test_match_proximity_strategy():
    """Test proximity strategy with zip codes"""
    print("\n=== Test 11: Proximity strategy ===")

    source = pd.Series({'zip': '12345'})

    # Exact match
    target1 = pd.Series({'zip': '12345'})
    match_fields = MatchFields(
        score_on=['zip'],
        weights=[FieldWeight(field='zip', weight=1.0)]
    )
    constraints = MatchConstraints()

    score1 = calculate_match_score(source, target1, MatchStrategy.PROXIMITY, match_fields, constraints)
    assert score1 == 1.0

    # Same prefix (nearby)
    target2 = pd.Series({'zip': '12399'})
    score2 = calculate_match_score(source, target2, MatchStrategy.PROXIMITY, match_fields, constraints)
    assert score2 == 0.7

    # Different area
    target3 = pd.Series({'zip': '98765'})
    score3 = calculate_match_score(source, target3, MatchStrategy.PROXIMITY, match_fields, constraints)
    assert score3 == 0.3

    print(f"✓ Proximity: exact={score1}, nearby={score2}, far={score3}")


def test_validation_missing_id():
    """Test validation catches missing id field"""
    print("\n=== Test 12: Validation - missing id ===")

    volunteers = pd.DataFrame([
        {'name': 'Alice', 'interests': ['music']}  # Missing 'id'
    ])

    roles = pd.DataFrame([
        {'id': 'r1', 'name': 'Role A', 'interests': ['music'], 'capacity': 1}
    ])

    match_fields = MatchFields(
        score_on=['interests'],
        weights=[FieldWeight(field='interests', weight=1.0)]
    )
    constraints = MatchConstraints()

    try:
        match(volunteers, roles, MatchStrategy.INTEREST_OVERLAP, match_fields, constraints)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert 'id' in str(e).lower()
        print(f"✓ Caught missing id: {e}")


def test_validation_missing_field():
    """Test validation catches missing match field"""
    print("\n=== Test 13: Validation - missing match field ===")

    volunteers = pd.DataFrame([
        {'id': 'v1', 'name': 'Alice'}  # Missing 'interests'
    ])

    roles = pd.DataFrame([
        {'id': 'r1', 'name': 'Role A', 'capacity': 1}  # Missing 'interests'
    ])

    match_fields = MatchFields(
        score_on=['interests'],
        weights=[FieldWeight(field='interests', weight=1.0)]
    )
    constraints = MatchConstraints()

    try:
        match(volunteers, roles, MatchStrategy.INTEREST_OVERLAP, match_fields, constraints)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert 'interests' in str(e)
        print(f"✓ Caught missing field: {e}")


def test_validation_weight_mismatch():
    """Test validation catches weight/score_on mismatch"""
    print("\n=== Test 14: Validation - weight mismatch ===")

    volunteers = pd.DataFrame([
        {'id': 'v1', 'name': 'Alice', 'interests': ['music']}
    ])

    roles = pd.DataFrame([
        {'id': 'r1', 'name': 'Role A', 'interests': ['music'], 'capacity': 1}
    ])

    # Weights don't match score_on fields
    match_fields = MatchFields(
        score_on=['interests'],
        weights=[FieldWeight(field='different_field', weight=1.0)]  # Mismatch!
    )
    constraints = MatchConstraints()

    try:
        match(volunteers, roles, MatchStrategy.INTEREST_OVERLAP, match_fields, constraints)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert 'mismatch' in str(e).lower()
        print(f"✓ Caught weight mismatch: {e}")


def test_empty_dataframes():
    """Test handling of empty DataFrames"""
    print("\n=== Test 15: Empty DataFrames ===")

    empty_df = pd.DataFrame(columns=['id', 'name', 'interests', 'capacity'])

    roles = pd.DataFrame([
        {'id': 'r1', 'name': 'Role A', 'interests': ['music'], 'capacity': 1}
    ])

    match_fields = MatchFields(
        score_on=['interests'],
        weights=[FieldWeight(field='interests', weight=1.0)]
    )
    constraints = MatchConstraints()

    # Empty source
    assignments = match(empty_df, roles, MatchStrategy.INTEREST_OVERLAP, match_fields, constraints)
    assert len(assignments) == 0

    # Empty target
    volunteers = pd.DataFrame([
        {'id': 'v1', 'name': 'Alice', 'interests': ['music']}
    ])
    assignments = match(volunteers, empty_df, MatchStrategy.INTEREST_OVERLAP, match_fields, constraints)
    assert len(assignments) == 0

    print("✓ Empty DataFrames handled correctly")


def run_all_tests():
    """Run all match tests"""
    print("=" * 60)
    print("Testing match.py functions (unit tests - no DB)")
    print("=" * 60)

    try:
        test_jaccard_similarity()
        test_score_single_field_arrays()
        test_score_single_field_strings()
        test_score_single_field_numbers()
        test_weighted_score_single_field()
        test_weighted_score_multiple_fields()
        test_match_interest_overlap()
        test_match_capacity_constraint()
        test_match_min_threshold()
        test_match_capacity_balanced_strategy()
        test_match_proximity_strategy()
        test_validation_missing_id()
        test_validation_missing_field()
        test_validation_weight_mismatch()
        test_empty_dataframes()

        print("\n" + "=" * 60)
        print("✓ All 15 match tests passed!")
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
