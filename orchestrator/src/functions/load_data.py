# src/functions/load_data.py
from src.database import fetch_all
from src.schemas import EntityType
from typing import Any, Optional, List
import pandas as pd


async def load_data(
    entity_type: EntityType,
    subtype: Optional[str] = None
) -> pd.DataFrame:
    """
    Load entities from database and return as DataFrame.

    This function ONLY loads data - no filtering beyond subtype.
    Use filter.py for all additional filtering.

    Args:
        entity_type: Which table to query (EntityType.PERSON, EntityType.GROUP, EntityType.GIFT)
        subtype: Optional row filter (e.g., 'volunteer', 'role', 'initiative')

    Returns:
        DataFrame with query results

    Examples:
        # Load all volunteers
        volunteers_df = await load_data(EntityType.PERSON, subtype='volunteer')

        # Load all roles
        roles_df = await load_data(EntityType.GROUP, subtype='role')

        # Load all gifts (no subtype)
        gifts_df = await load_data(EntityType.GIFT)
    """
    # Start building query
    query = f"SELECT * FROM {entity_type.value}"
    params: List[Any] = []

    # Add subtype filter (only filtering we do at SQL level)
    if subtype:
        if entity_type == EntityType.PERSON:
            query += " WHERE person_type = $1"
            params.append(subtype)
        elif entity_type == EntityType.GROUP:
            query += " WHERE group_type = $1"
            params.append(subtype)
        # EntityType.GIFT has no subtype column

    # Execute query
    rows = await fetch_all(query, *params)

    # Convert to DataFrame
    return pd.DataFrame(rows)


