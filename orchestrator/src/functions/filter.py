# src/functions/filter.py
import pandas as pd
from typing import List, Union, Any
from datetime import datetime, timedelta
from src.schemas import FilterCondition


def filter_data(
    df: pd.DataFrame,
    filters: Union[List[FilterCondition], List[dict]]
) -> pd.DataFrame:
    """
    Apply filters to DataFrame.

    This is the main filtering function - all filtering happens here,
    not in load_data(). Supports both FilterCondition objects (from LLM)
    and dict format (for manual testing).

    Args:
        df: DataFrame to filter
        filters: List of FilterCondition objects or dicts with keys:
            - field: str - Field name to filter on
            - operator: str - One of: =, >, >=, <, <=, !=, contains
            - value: str - Value to compare (will be converted to proper type)

    Returns:
        Filtered DataFrame

    Examples:
        from src.schemas import FilterCondition

        # Filter volunteers available on Wednesday
        filters = [FilterCondition(field='availability_days', operator='contains', value='Wed')]
        wednesday_volunteers = filter_data(volunteers_df, filters)

        # Filter roles with capacity > 0
        filters = [FilterCondition(field='capacity', operator='>', value='0')]
        available_roles = filter_data(roles_df, filters)

        # Multiple filters (AND logic)
        filters = [
            FilterCondition(field='availability_days', operator='contains', value='Sun'),
            FilterCondition(field='capacity', operator='>', value='0')
        ]
        result = filter_data(volunteers_df, filters)
    """
    result = df.copy()

    for fc in filters:
        # Extract filter attributes (handles both objects and dicts)
        field = fc.field if hasattr(fc, 'field') else fc['field']
        operator = fc.operator if hasattr(fc, 'operator') else fc['operator']
        value = fc.value if hasattr(fc, 'value') else fc['value']

        # Convert value to appropriate type
        value = _convert_value(value, field)

        # Apply filter based on operator
        if operator == '=':
            result = result[result[field] == value]

        elif operator == '>':
            result = result[result[field] > value]

        elif operator == '>=':
            result = result[result[field] >= value]

        elif operator == '<':
            result = result[result[field] < value]

        elif operator == '<=':
            result = result[result[field] <= value]

        elif operator == '!=':
            result = result[result[field] != value]

        elif operator == 'contains':
            # For array fields (like interests, availability_days)
            result = result[
                result[field].apply(
                    lambda x: value in x if isinstance(x, list) else False
                )
            ]

        else:
            raise ValueError(f"Unsupported operator: {operator}")

    return result


def filter_by_time_condition(
    df: pd.DataFrame,
    time_field: str,
    threshold: str,
    operator: str = '>',
    additional_filters: List[str] = None
) -> pd.DataFrame:
    """
    Filter DataFrame by relative time condition.

    Used by monitoring template for time-based filtering like
    "visitors from more than 14 days ago".

    Args:
        df: DataFrame to filter
        time_field: Name of the datetime field (e.g., 'visit_date')
        threshold: Relative time string (e.g., '14 days', '90 days', '2 weeks')
        operator: Comparison operator (>, <, >=, <=)
        additional_filters: Optional SQL-like conditions (e.g., ['last_contact_date IS NULL'])

    Returns:
        Filtered DataFrame

    Examples:
        # Visitors from more than 14 days ago
        flagged = filter_by_time_condition(
            visitors_df,
            time_field='visit_date',
            threshold='14 days',
            operator='>'
        )

        # Donors who gave in last 30 days
        recent = filter_by_time_condition(
            gifts_df,
            time_field='gift_date',
            threshold='30 days',
            operator='<'
        )
    """
    # Parse threshold (e.g., "14 days" → 14, "days")
    parts = threshold.split()
    if len(parts) != 2:
        raise ValueError(f"Invalid threshold format: '{threshold}'. Expected 'N days|weeks|months'")

    try:
        amount = int(parts[0])
    except ValueError:
        raise ValueError(f"Invalid threshold amount: '{parts[0]}'. Must be a number")

    unit = parts[1].rstrip('s').lower()  # "days" → "day", "Weeks" → "week"

    # Calculate cutoff date
    if unit == 'day':
        delta = timedelta(days=amount)
    elif unit == 'week':
        delta = timedelta(weeks=amount)
    elif unit == 'month':
        delta = timedelta(days=amount * 30)  # Approximate
    else:
        raise ValueError(f"Unsupported time unit: '{unit}'. Use 'days', 'weeks', or 'months'")

    cutoff_date = datetime.now() - delta

    # Apply time filter based on operator
    result = df.copy()

    if operator == '>':
        # Time SINCE event > threshold (event was BEFORE cutoff)
        result = result[result[time_field] < cutoff_date]
    elif operator == '<':
        # Time SINCE event < threshold (event was AFTER cutoff)
        result = result[result[time_field] > cutoff_date]
    elif operator == '>=':
        result = result[result[time_field] <= cutoff_date]
    elif operator == '<=':
        result = result[result[time_field] >= cutoff_date]
    else:
        raise ValueError(f"Unsupported operator for time filtering: {operator}")

    # Apply additional filters if provided
    if additional_filters:
        for filter_str in additional_filters:
            filter_str = filter_str.strip()

            # Handle "IS NULL" checks
            if 'IS NULL' in filter_str:
                col = filter_str.split(' IS NULL')[0].strip()
                result = result[result[col].isna()]

            # Handle "IS NOT NULL" checks
            elif 'IS NOT NULL' in filter_str:
                col = filter_str.split(' IS NOT NULL')[0].strip()
                result = result[result[col].notna()]

            # Can add more SQL-like conditions here as needed
            else:
                raise ValueError(f"Unsupported additional filter: '{filter_str}'")

    return result


def _convert_value(value: str, field: str) -> Any:
    """
    Convert string value to appropriate Python type based on field name.

    Args:
        value: String value from LLM extraction or manual input
        field: Field name for type inference

    Returns:
        Converted value (int, float, datetime, or original string)
    """
    # Date/datetime fields
    if field.endswith(('_date', '_at')):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass  # Keep as string if can't parse

    # Numeric fields - try to convert any numeric-looking value
    try:
        # Try int first
        if '.' not in str(value):
            return int(value)
        # Otherwise float
        return float(value)
    except (ValueError, TypeError):
        pass  # Keep as original if can't parse as number

    # Boolean fields
    if isinstance(value, str) and value.lower() in ['true', 'false']:
        return value.lower() == 'true'

    # Keep as string for everything else
    return value
