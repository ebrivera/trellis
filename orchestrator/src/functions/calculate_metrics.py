# src/functions/calculate_metrics.py
import pandas as pd
from typing import Dict, List, Any
from src.database import fetch_all

async def calculate_metrics(
    formulas: List[Dict[str, Any]],
    source_data: pd.DataFrame = None
) -> Dict[str, Any]:
    """
    Calculate metrics based on formulas.
    For giving analysis, queries gifts table directly.
    """
    results = {}
    
    for formula in formulas:
        name = formula['name']
        formula_str = formula['formula']
        group_by = formula.get('group_by')
        
        if 'SUM(amount)' in formula_str:
            if source_data is not None:
                if group_by:
                    grouped = source_data.groupby(group_by)['amount'].sum()
                    results[name] = grouped.to_dict()
                else:
                    results[name] = float(source_data['amount'].sum())
        
        elif 'COUNT' in formula_str:
            if source_data is not None:
                if 'DISTINCT' in formula_str:
                    col = formula_str.split('(')[-1].split(')')[0]
                    results[name] = int(source_data[col].nunique())
                else:
                    results[name] = len(source_data)
        
        elif 'AVG' in formula_str:
            if source_data is not None:
                col = formula_str.split('(')[-1].split(')')[0]
                results[name] = float(source_data[col].mean())
    
    return results