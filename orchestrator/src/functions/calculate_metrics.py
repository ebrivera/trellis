# src/functions/calculate_metrics.py
import pandas as pd
import re
from typing import Dict, Any, Union
from ..templates.analysis import MetricFormula


def calculate_metrics(
    formulas: list[MetricFormula],
    source_data: pd.DataFrame
) -> Dict[str, Any]:
    """
    Calculate metrics based on formulas.

    Supports:
    - Basic aggregations: SUM, AVG, COUNT, MIN, MAX
    - COUNT DISTINCT for unique counts
    - Grouping via group_by field
    - Calculated metrics referencing other metrics or columns
    - Result formatting (currency, percent, number)

    Args:
        formulas: List of MetricFormula objects defining what to calculate
        source_data: DataFrame to calculate metrics on

    Returns:
        Dictionary mapping metric names to results

    Examples:
        # Simple aggregation
        MetricFormula(name='total_raised', formula='SUM(amount)')
        # => {'total_raised': 15000.0}

        # With grouping
        MetricFormula(name='total_by_initiative', formula='SUM(amount)', group_by='initiative_name')
        # => {'total_by_initiative': {'Building Fund': 5000, 'Youth Program': 10000}}

        # Calculated metric
        MetricFormula(name='avg_gift', formula='total_raised / donor_count')
        # => {'avg_gift': 150.0}
    """
    results = {}
    formats_to_apply = {}  # Track which metrics need formatting (apply after all calculations)

    for formula in formulas:
        try:
            # Check if this is a calculated metric (references other metrics/columns with operators)
            if _is_calculated_metric(formula.formula):
                # Check if it's grouped or ungrouped
                if formula.group_by:
                    result = _calculate_grouped_expression(formula, source_data, results)
                else:
                    result = _calculate_expression(formula, source_data, results)
            else:
                # Parse and execute aggregation
                result = _calculate_aggregation(formula, source_data)

            # Store raw numeric result (don't format yet - derived metrics need raw values)
            results[formula.name] = result

            # Track formatting to apply after all calculations complete
            if formula.format in ['currency', 'percent', 'number']:
                formats_to_apply[formula.name] = formula.format

        except Exception as e:
            # Store error but continue processing other formulas
            results[formula.name] = {'error': str(e)}

    # Apply formatting after all calculations are complete
    # This ensures derived metrics can reference raw numeric values
    for metric_name, format_type in formats_to_apply.items():
        if metric_name in results:
            # Only format if no error
            if not (isinstance(results[metric_name], dict) and 'error' in results[metric_name]):
                results[metric_name] = _format_result(results[metric_name], format_type)

    return results


def _is_calculated_metric(formula: str) -> bool:
    """
    Check if formula is a calculated metric (references other metrics/columns).

    Calculated metrics contain operators (+, -, *, /) but NO aggregation functions.
    """
    # Has arithmetic operators
    has_operators = any(op in formula for op in ['+', '-', '*', '/'])

    # Does NOT have aggregation functions
    has_aggregation = bool(re.match(r'^\s*(SUM|AVG|COUNT|MIN|MAX)\s*\(', formula, re.IGNORECASE))

    return has_operators and not has_aggregation


def _calculate_aggregation(
    formula: MetricFormula,
    df: pd.DataFrame
) -> Union[float, int, Dict[str, Any]]:
    """
    Calculate a single aggregation (SUM, AVG, COUNT, MIN, MAX).

    Returns:
        - Single value if no grouping
        - Dictionary of {group: value} if grouped
    """
    # Extract GROUP BY from formula string if present
    group_by = formula.group_by
    formula_str = formula.formula

    # Handle "GROUP BY" in formula string (for backward compatibility)
    if 'GROUP BY' in formula_str.upper():
        parts = re.split(r'\s+GROUP\s+BY\s+', formula_str, flags=re.IGNORECASE)
        formula_str = parts[0].strip()
        if not group_by:  # Only use if not already specified
            group_by = parts[1].strip()

    # Parse aggregation function
    match = re.match(
        r'^\s*(SUM|AVG|COUNT|MIN|MAX)\s*\(\s*(.+?)\s*\)\s*$',
        formula_str,
        re.IGNORECASE
    )

    if not match:
        raise ValueError(f"Invalid aggregation formula: '{formula_str}'. Expected format: 'OPERATION(column)'")

    operation = match.group(1).upper()
    argument = match.group(2).strip()

    # Validate column exists (unless it's COUNT(*))
    if argument != '*' and argument.upper() != 'DISTINCT *':
        # Extract column name from DISTINCT if present
        if argument.upper().startswith('DISTINCT '):
            col_name = argument[9:].strip()  # Remove "DISTINCT "
        else:
            col_name = argument

        if col_name not in df.columns:
            raise ValueError(f"Column '{col_name}' not found in DataFrame. Available: {list(df.columns)}")

    # Apply aggregation
    if group_by:
        return _apply_grouped_aggregation(df, operation, argument, group_by)
    else:
        return _apply_single_aggregation(df, operation, argument)


def _apply_single_aggregation(
    df: pd.DataFrame,
    operation: str,
    argument: str
) -> Union[float, int]:
    """Apply aggregation to entire DataFrame (no grouping)."""

    if operation == 'COUNT':
        if argument == '*':
            return len(df)
        elif argument.upper().startswith('DISTINCT '):
            col = argument[9:].strip()
            return int(df[col].nunique())
        else:
            # COUNT(column) - count non-null values
            return int(df[argument].count())

    elif operation == 'SUM':
        return float(df[argument].sum())

    elif operation == 'AVG':
        return float(df[argument].mean())

    elif operation == 'MIN':
        return float(df[argument].min())

    elif operation == 'MAX':
        return float(df[argument].max())

    raise ValueError(f"Unsupported operation: {operation}")


def _apply_grouped_aggregation(
    df: pd.DataFrame,
    operation: str,
    argument: str,
    group_by: str
) -> Dict[str, Any]:
    """Apply aggregation with GROUP BY."""

    # Validate group_by column exists
    if group_by not in df.columns:
        raise ValueError(f"Group by column '{group_by}' not found. Available: {list(df.columns)}")

    if operation == 'COUNT':
        if argument == '*':
            grouped = df.groupby(group_by).size()
        elif argument.upper().startswith('DISTINCT '):
            col = argument[9:].strip()
            grouped = df.groupby(group_by)[col].nunique()
        else:
            grouped = df.groupby(group_by)[argument].count()

    elif operation == 'SUM':
        grouped = df.groupby(group_by)[argument].sum()

    elif operation == 'AVG':
        grouped = df.groupby(group_by)[argument].mean()

    elif operation == 'MIN':
        grouped = df.groupby(group_by)[argument].min()

    elif operation == 'MAX':
        grouped = df.groupby(group_by)[argument].max()

    else:
        raise ValueError(f"Unsupported operation: {operation}")

    # Convert to dict with proper types
    return {str(k): float(v) if pd.api.types.is_numeric_dtype(type(v)) else v
            for k, v in grouped.to_dict().items()}


def _calculate_expression(
    formula: MetricFormula,
    df: pd.DataFrame,
    calculated_metrics: Dict[str, Any]
) -> Union[float, int]:
    """
    Calculate a metric that references other metrics or columns.

    Uses pandas eval() for safe evaluation.
    Only allows access to calculated metrics and DataFrame columns.
    """
    expression = formula.formula

    # Build safe context with calculated metrics and DataFrame columns
    context = {}

    # Add previously calculated metrics
    for metric_name, metric_value in calculated_metrics.items():
        # Skip if metric has error
        if isinstance(metric_value, dict) and 'error' in metric_value:
            continue
        # Only add scalar metrics (not grouped results)
        if not isinstance(metric_value, dict):
            context[metric_name] = metric_value

    # Add DataFrame columns as single values (for ungrouped calculations)
    # If we need column access, we'd need to handle this differently
    # For now, assume calculated metrics reference other metrics only

    # Validate that all referenced names exist
    # Extract identifiers from expression
    identifiers = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', expression)

    for identifier in identifiers:
        if identifier not in context and identifier not in df.columns:
            raise ValueError(
                f"Unknown reference '{identifier}' in formula '{expression}'. "
                f"Available metrics: {list(calculated_metrics.keys())}, "
                f"Available columns: {list(df.columns)}"
            )
        # Add column aggregates if needed (use first value for single-row results)
        if identifier in df.columns and identifier not in context:
            # For calculated metrics, assume we want a scalar
            # This is a simplification - might need more sophisticated handling
            context[identifier] = df[identifier].iloc[0] if len(df) > 0 else 0

    # Safely evaluate expression
    try:
        # Use Python eval with restricted context (no builtins)
        result = eval(expression, {"__builtins__": {}}, context)
        return float(result)
    except Exception as e:
        raise ValueError(f"Error evaluating expression '{expression}': {e}")


def _calculate_grouped_expression(
    formula: MetricFormula,
    df: pd.DataFrame,
    calculated_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate a derived metric that has group_by.

    For each group value:
    1. Get the values of referenced metrics for that group
    2. Get column values for that group (from first row)
    3. Evaluate the expression

    Args:
        formula: MetricFormula with group_by specified
        df: Source DataFrame
        calculated_metrics: Previously calculated metrics

    Returns:
        Dict mapping group values to calculated results
    """
    expression = formula.formula
    group_by = formula.group_by

    if not group_by or group_by not in df.columns:
        raise ValueError(f"Group by column '{group_by}' not found in DataFrame")

    # Get all unique group values
    groups = df[group_by].unique()
    results = {}

    # Extract identifiers from expression to know what we need
    identifiers = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', expression)

    for group_value in groups:
        # Build context for this specific group
        context = {}

        # Add values from calculated metrics
        for identifier in identifiers:
            if identifier in calculated_metrics:
                metric_value = calculated_metrics[identifier]

                # If the metric is grouped, get the value for this specific group
                if isinstance(metric_value, dict):
                    # Skip if this group doesn't have a value in the metric
                    if str(group_value) in metric_value:
                        context[identifier] = metric_value[str(group_value)]
                    else:
                        # Try without string conversion
                        context[identifier] = metric_value.get(group_value, 0)
                else:
                    # Scalar metric - use as is
                    context[identifier] = metric_value

            # Add column values for this group (use first row of group)
            elif identifier in df.columns:
                group_df = df[df[group_by] == group_value]
                if len(group_df) > 0:
                    context[identifier] = group_df[identifier].iloc[0]

        # Validate all identifiers are available
        missing = [id for id in identifiers if id not in context]
        if missing:
            raise ValueError(
                f"Unknown references {missing} in formula '{expression}' for group '{group_value}'. "
                f"Available metrics: {list(calculated_metrics.keys())}, "
                f"Available columns: {list(df.columns)}"
            )

        # Evaluate expression for this group
        try:
            result = eval(expression, {"__builtins__": {}}, context)
            results[str(group_value)] = float(result)
        except Exception as e:
            raise ValueError(f"Error evaluating '{expression}' for group '{group_value}': {e}")

    return results


def _format_result(
    result: Union[float, int, Dict[str, Any]],
    format_type: str
) -> Union[str, Dict[str, str]]:
    """
    Format result according to format type.

    Args:
        result: Raw numeric result or dict of results
        format_type: 'currency', 'percent', or 'number'

    Returns:
        Formatted string or dict of formatted strings
    """
    def format_single(value: Union[float, int]) -> str:
        if format_type == 'currency':
            return f"${value:,.2f}"
        elif format_type == 'percent':
            return f"{value * 100:.1f}%"
        elif format_type == 'number':
            return f"{value:,.0f}"
        return str(value)

    # Handle grouped results (dict)
    if isinstance(result, dict):
        return {k: format_single(v) for k, v in result.items()}

    # Handle single result
    return format_single(result)


def _validate_formula(formula: MetricFormula, df: pd.DataFrame) -> None:
    """
    Validate that formula can be executed on DataFrame.

    Raises ValueError if validation fails.
    """
    # This is called implicitly during calculation
    # Could be made explicit for early validation
    pass
