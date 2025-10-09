# src/functions/match.py
import pandas as pd
from typing import List, Dict, Any, Set, Union
from ..schemas import MatchStrategy
from ..templates.matching import MatchFields, MatchConstraints


def match(
    source_df: pd.DataFrame,
    target_df: pd.DataFrame,
    strategy: MatchStrategy,
    match_fields: MatchFields,
    constraints: MatchConstraints
) -> List[Dict[str, Any]]:
    """
    Match source entities to targets based on strategy and field configuration.

    Args:
        source_df: DataFrame of entities to be assigned (volunteers, mentees)
        target_df: DataFrame of targets to assign to (roles, mentors)
        strategy: Matching algorithm (interest_overlap, capacity_balanced, proximity)
        match_fields: Which fields to score on and their weights
        constraints: Matching constraints (capacity, thresholds, preferences)

    Returns:
        List of assignments with scores

    Examples:
        # Match volunteers to roles based on interests (60%) and zip code (40%)
        match_fields = MatchFields(
            score_on=['interests', 'zip'],
            weights=[
                FieldWeight(field='interests', weight=0.6),
                FieldWeight(field='zip', weight=0.4)
            ]
        )
        constraints = MatchConstraints(
            max_per_target='capacity',
            min_score_threshold=0.3
        )
        assignments = match(
            volunteers_df,
            roles_df,
            MatchStrategy.INTEREST_OVERLAP,
            match_fields,
            constraints
        )
    """
    # Validate required fields exist
    _validate_dataframes(source_df, target_df, match_fields, constraints)

    assignments = []
    target_capacity = _initialize_capacity_tracking(target_df, constraints)

    # Match each source to best available target
    for _, source in source_df.iterrows():
        best_target_id = None
        best_score = 0.0

        for _, target in target_df.iterrows():
            # Skip if target at capacity
            if target_capacity[target['id']] <= 0:
                continue

            # Calculate match score using strategy and field configuration
            score = calculate_match_score(source, target, strategy, match_fields, constraints)

            # Check minimum threshold
            min_threshold = constraints.min_score_threshold or 0.0
            if score < min_threshold:
                continue

            # Update best match
            if score > best_score:
                best_score = score
                best_target_id = target['id']

        # Record assignment if match found
        if best_target_id:
            target_row = target_df[target_df['id'] == best_target_id].iloc[0]
            assignments.append({
                'source_id': str(source['id']),
                'target_id': str(best_target_id),
                'match_score': round(best_score, 2),
                'source_name': source.get('name'),
                'target_name': target_row.get('name')
            })
            target_capacity[best_target_id] -= 1

    return assignments


def calculate_match_score(
    source: pd.Series,
    target: pd.Series,
    strategy: MatchStrategy,
    match_fields: MatchFields,
    constraints: MatchConstraints
) -> float:
    """
    Calculate similarity score between source and target.

    Strategy determines HOW to calculate the score.
    MatchFields determines WHAT fields to use and their weights.
    """

    if strategy == MatchStrategy.INTEREST_OVERLAP:
        # Pure weighted field scoring
        return _calculate_weighted_score(source, target, match_fields)

    elif strategy == MatchStrategy.CAPACITY_BALANCED:
        # Combine field scoring with capacity preference
        field_score = _calculate_weighted_score(source, target, match_fields)

        # Bonus for targets with more remaining capacity (encourages load balancing)
        capacity = target.get('capacity', 0)
        # Handle None/NaN capacity values
        if capacity is not None and pd.notna(capacity) and capacity > 0:
            # Add bonus scaled to capacity: ln(capacity+1) / 20
            # This gives: cap=1 → 0.035, cap=10 → 0.12, cap=50 → 0.20, cap=100 → 0.23
            import math
            capacity_bonus = min(0.25, math.log(capacity + 1) / 20.0)
            return min(1.0, field_score + capacity_bonus)

        return field_score

    elif strategy == MatchStrategy.PROXIMITY:
        # Geographic distance-based scoring
        return _calculate_proximity_score(source, target, match_fields)

    return 0.5  # Fallback


def _calculate_weighted_score(
    source: pd.Series,
    target: pd.Series,
    match_fields: MatchFields
) -> float:
    """
    Calculate weighted average score across multiple fields.

    Returns:
        Weighted score between 0.0 and 1.0
    """
    # If no fields to score, return neutral score (pure capacity balancing)
    if len(match_fields.score_on) == 0:
        return 0.5  # Neutral score when not scoring any fields
    
    total_score = 0.0

    # Build weight map for quick lookup
    weight_map = {fw.field: fw.weight for fw in match_fields.weights}

    for field_name in match_fields.score_on:
        # Get weight for this field (default to equal weights if not specified)
        weight = weight_map.get(field_name, 1.0 / len(match_fields.score_on))

        # Calculate score for this field
        field_score = _score_single_field(source, target, field_name)

        # Add weighted score
        total_score += field_score * weight

    return min(1.0, total_score)  # Cap at 1.0


def _score_single_field(
    source: pd.Series,
    target: pd.Series,
    field_name: str
) -> float:
    """
    Score similarity for a single field.
    Handles different data types: arrays, strings, numbers.

    Returns:
        Score between 0.0 and 1.0
    """
    
    field_mapping = {
        'interests': ['interests', 'requirements'],  # volunteer.interests ↔ role.requirements
        'requirements': ['interests', 'requirements'],
    }
    
    source_val = source.get(field_name)
    target_val = target.get(field_name)

    # If target doesn't have the field, try mapped alternatives
    if target_val is None and field_name in field_mapping:
        for alt_field in field_mapping[field_name]:
            if alt_field != field_name:  # Don't retry the same field
                target_val = target.get(alt_field)
                if target_val is not None:
                    break

    # Handle missing values (use try/except to avoid issues with arrays)
    try:
        if pd.isna(source_val) or pd.isna(target_val):
            return 0.0
    except (ValueError, TypeError):
        # For arrays or complex types, check if None
        if source_val is None or target_val is None:
            return 0.0

    # Array fields (e.g., interests, skills) - use Jaccard similarity
    if isinstance(source_val, list) and isinstance(target_val, list):
        return _jaccard_similarity(source_val, target_val)

    # String fields - exact match or substring
    if isinstance(source_val, str) and isinstance(target_val, str):
        if source_val.lower() == target_val.lower():
            return 1.0
        elif source_val.lower() in target_val.lower() or target_val.lower() in source_val.lower():
            return 0.5
        return 0.0

    # Numeric fields - normalized distance
    try:
        source_num = float(source_val)
        target_num = float(target_val)
        # If values are close, score higher (within 10% = 1.0, further = lower)
        diff = abs(source_num - target_num)
        max_val = max(source_num, target_num)
        if max_val == 0:
            return 1.0 if diff == 0 else 0.0
        similarity = 1.0 - min(1.0, diff / max_val)
        return similarity
    except (ValueError, TypeError):
        pass

    # Default: exact equality
    return 1.0 if source_val == target_val else 0.0


def _jaccard_similarity(list1: List, list2: List) -> float:
    """
    Calculate Jaccard similarity between two lists.

    Jaccard = |intersection| / |union|

    Returns:
        Score between 0.0 and 1.0
    """
    set1 = set(list1)
    set2 = set(list2)

    if not set1 or not set2:
        return 0.0

    intersection = len(set1 & set2)
    union = len(set1 | set2)

    return intersection / union if union > 0 else 0.0


def _calculate_proximity_score(
    source: pd.Series,
    target: pd.Series,
    match_fields: MatchFields
) -> float:
    """
    Calculate geographic proximity score based on zip codes or coordinates.

    For MVP: Simple zip code prefix matching.
    Future: Use actual geocoding and distance calculation.
    """
    # Try to find a location field in match_fields
    for field_name in match_fields.score_on:
        if 'zip' in field_name.lower() or 'postal' in field_name.lower():
            source_zip = str(source.get(field_name, ''))
            target_zip = str(target.get(field_name, ''))

            if not source_zip or not target_zip:
                continue

            # Exact match
            if source_zip == target_zip:
                return 1.0

            # Same prefix (first 3 digits) - nearby area
            if len(source_zip) >= 3 and len(target_zip) >= 3:
                if source_zip[:3] == target_zip[:3]:
                    return 0.7

            # Different area
            return 0.3

    # No location field found, fall back to other fields
    return _calculate_weighted_score(source, target, match_fields)


def _initialize_capacity_tracking(
    target_df: pd.DataFrame,
    constraints: MatchConstraints
) -> Dict[Any, int]:
    """
    Initialize capacity tracking for each target.

    Returns:
        Dictionary mapping target_id to remaining capacity
    """
    capacity_map = {}

    for _, target in target_df.iterrows():
        target_id = target['id']

        # Check if capacity field is specified
        if constraints.max_per_target:
            capacity_field = constraints.max_per_target
            if capacity_field in target:
                capacity_value = target[capacity_field]
                # Handle None, NaN, or empty values
                if pd.notna(capacity_value) and capacity_value not in (None, ''):
                    try:
                        capacity_map[target_id] = int(capacity_value)
                    except (ValueError, TypeError):
                        capacity_map[target_id] = 999  # Unlimited if can't convert
                else:
                    capacity_map[target_id] = 999  # Unlimited if null
            else:
                capacity_map[target_id] = 999  # Unlimited if field missing
        else:
            capacity_map[target_id] = 999  # Unlimited if not specified

    return capacity_map


def _validate_dataframes(
    source_df: pd.DataFrame,
    target_df: pd.DataFrame,
    match_fields: MatchFields,
    constraints: MatchConstraints
) -> None:
    """
    Validate that required fields exist in DataFrames.
    Raises ValueError with clear message if validation fails.
    """
    # Check for 'id' field
    if 'id' not in source_df.columns:
        raise ValueError("source_df must have 'id' column")
    if 'id' not in target_df.columns:
        raise ValueError("target_df must have 'id' column")

    # Check that match fields exist in at least one DataFrame
    for field_name in match_fields.score_on:
        source_has = field_name in source_df.columns
        target_has = field_name in target_df.columns

        if not source_has and not target_has:
            raise ValueError(
                f"Field '{field_name}' not found in source or target DataFrames. "
                f"Available in source: {list(source_df.columns)}, "
                f"Available in target: {list(target_df.columns)}"
            )

    # Check capacity field if specified
    if constraints.max_per_target:
        if constraints.max_per_target not in target_df.columns:
            raise ValueError(
                f"Capacity field '{constraints.max_per_target}' not found in target_df. "
                f"Available columns: {list(target_df.columns)}"
            )

    # Validate weights match score_on fields
    weight_fields = {fw.field for fw in match_fields.weights}
    score_fields = set(match_fields.score_on)

    if weight_fields != score_fields:
        raise ValueError(
            f"Mismatch between score_on fields {score_fields} and weight fields {weight_fields}. "
            f"They must be identical."
        )
