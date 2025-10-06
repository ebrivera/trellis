# src/functions/load_data.py
from src.database import fetch_all
from typing import List, Dict, Any, Optional
import pandas as pd

async def load_data(
    entity_type: str,
    filters: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Load entities from database.
    entity_type: 'volunteer', 'visitor', 'donor', 'mentor', 'mentee'
    filters: SQL WHERE conditions like ["availability_days && ARRAY['Sun']"]
    """
    query = "SELECT * FROM people WHERE person_type = $1"
    
    if filters:
        for filter_condition in filters:
            query += f" AND {filter_condition}"
    
    rows = await fetch_all(query, entity_type)
    return pd.DataFrame(rows)


async def load_groups(
    group_type: str,
    filters: Optional[List[str]] = None
) -> pd.DataFrame:
    """Load groups (roles, initiatives) from database."""
    query = "SELECT * FROM groups WHERE group_type = $1"
    
    if filters:
        for filter_condition in filters:
            query += f" AND {filter_condition}"
    
    rows = await fetch_all(query, group_type)
    return pd.DataFrame(rows)