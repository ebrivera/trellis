# src/functions/filter.py
import pandas as pd
from typing import List

def filter_data(df: pd.DataFrame, conditions: List[str]) -> pd.DataFrame:
    """
    Apply filter conditions to dataframe.
    For hackathon: support basic conditions extracted by LLM.
    """
    filtered_df = df.copy()
    
    for condition in conditions:
        # Parse simple conditions
        if "LIKE" in condition:
            # e.g., "availability_days LIKE '%Sun%'"
            field = condition.split(" LIKE ")[0].strip()
            value = condition.split("'")[1]  # Extract value between quotes
            filtered_df = filtered_df[
                filtered_df[field].apply(lambda x: value in str(x) if x else False)
            ]
        
        elif ">" in condition or "<" in condition:
            # Handle date comparisons
            # Already filtered at query level for demo
            pass
    
    return filtered_df