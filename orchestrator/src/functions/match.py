# src/functions/match.py
import pandas as pd
from typing import Dict, List, Any

def match(
    source_df: pd.DataFrame,
    target_df: pd.DataFrame,
    strategy: str,
    constraints: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Match source entities to targets based on strategy.
    Returns list of assignments with scores.
    """
    assignments = []
    target_capacity = {}  # Track remaining capacity
    
    # Initialize capacity tracking
    for _, target in target_df.iterrows():
        capacity = constraints.get('max_per_target')
        if capacity and capacity in target:
            target_capacity[target['id']] = target[capacity]
        else:
            target_capacity[target['id']] = 999  # Unlimited
    
    # Match each source to best target
    for _, source in source_df.iterrows():
        best_target_id = None
        best_score = 0.0
        
        for _, target in target_df.iterrows():
            # Skip if target at capacity
            if target_capacity[target['id']] <= 0:
                continue
            
            # Calculate match score based on strategy
            score = calculate_match_score(source, target, strategy)
            
            # Check minimum threshold
            min_threshold = constraints.get('min_score_threshold', 0.0)
            if score < min_threshold:
                continue
            
            if score > best_score:
                best_score = score
                best_target_id = target['id']
        
        # Record assignment if match found
        if best_target_id:
            assignments.append({
                'source_id': str(source['id']),
                'target_id': str(best_target_id),
                'match_score': round(best_score, 2),
                'source_name': source.get('name'),
                'target_name': target_df[target_df['id'] == best_target_id]['name'].iloc[0]
            })
            target_capacity[best_target_id] -= 1
    
    return assignments


def calculate_match_score(source: pd.Series, target: pd.Series, strategy: str) -> float:
    """Calculate similarity score between source and target."""
    
    if strategy == 'interest_overlap':
        # Compare interests/requirements arrays
        source_interests = set(source.get('interests', []) or [])
        target_reqs = set(target.get('requirements', []) or [])
        
        if not source_interests or not target_reqs:
            return 0.0
        
        overlap = len(source_interests & target_reqs)
        total = len(source_interests | target_reqs)
        return overlap / total if total > 0 else 0.0
    
    elif strategy == 'capacity_balanced':
        # Simple score - can be enhanced with other factors
        return 0.75  # Base score, would add interest overlap
    
    elif strategy == 'proximity':
        # Would compare zip codes, for now return random
        return 0.6
    
    return 0.5  # Default