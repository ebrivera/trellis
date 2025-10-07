"""
Database connection and query utilities for Supabase PostgreSQL.
Uses asyncpg for async connection pooling.
"""

import asyncpg
import os
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connection pool (initialized on startup)
_pool: Optional[asyncpg.Pool] = None


async def init_db_pool():
    """Initialize the database connection pool."""
    global _pool
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    _pool = await asyncpg.create_pool(
        database_url,
        min_size=2,
        max_size=10,
        command_timeout=60
    )
    print(f"✓ Database pool initialized")


async def close_db_pool():
    """Close the database connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        print("✓ Database pool closed")


def get_pool() -> asyncpg.Pool:
    """Get the connection pool."""
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call init_db_pool() first.")
    return _pool


@asynccontextmanager
async def get_connection():
    """Context manager for getting a database connection from the pool."""
    pool = get_pool()
    async with pool.acquire() as connection:
        yield connection


async def fetch_all(query: str, *args) -> List[Dict[str, Any]]:
    """
    Execute a SELECT query and return all rows as a list of dicts.
    
    Example:
        rows = await fetch_all("SELECT * FROM people WHERE person_type = $1", "volunteer")
    """
    async with get_connection() as conn:
        rows = await conn.fetch(query, *args)
        return [dict(row) for row in rows]


async def fetch_one(query: str, *args) -> Optional[Dict[str, Any]]:
    """
    Execute a SELECT query and return the first row as a dict, or None.
    
    Example:
        person = await fetch_one("SELECT * FROM people WHERE id = $1", person_id)
    """
    async with get_connection() as conn:
        row = await conn.fetchrow(query, *args)
        return dict(row) if row else None


async def execute(query: str, *args) -> str:
    """
    Execute a query that doesn't return rows (INSERT, UPDATE, DELETE).
    Returns the query status string.
    
    Example:
        await execute("UPDATE people SET name = $1 WHERE id = $2", "John", person_id)
    """
    async with get_connection() as conn:
        result = await conn.execute(query, *args)
        return result


async def insert_one(table: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Insert a single row and return the inserted row with generated fields.
    
    Example:
        person = await insert_one("people", {
            "name": "John",
            "email": "john@example.com",
            "person_type": "volunteer"
        })
    """
    # Convert dict values to proper types for PostgreSQL
    data = _prepare_data(data)
    
    columns = ", ".join(data.keys())
    placeholders = ", ".join(f"${i+1}" for i in range(len(data)))
    values = list(data.values())
    
    query = f"""
        INSERT INTO {table} ({columns})
        VALUES ({placeholders})
        RETURNING *
    """
    
    async with get_connection() as conn:
        row = await conn.fetchrow(query, *values)
        return dict(row)


async def insert_many(table: str, rows: List[Dict[str, Any]]) -> int:
    """
    Insert multiple rows efficiently.
    Returns the number of rows inserted.
    
    Example:
        count = await insert_many("assignments", [
            {"source_id": id1, "target_id": id2, "assignment_type": "volunteer_to_role"},
            {"source_id": id3, "target_id": id4, "assignment_type": "volunteer_to_role"}
        ])
    """
    if not rows:
        return 0
    
    # All rows must have same columns
    columns = list(rows[0].keys())
    
    async with get_connection() as conn:
        # Prepare insert statement
        placeholders = ", ".join(f"${i+1}" for i in range(len(columns)))
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
        
        # Execute many
        prepared_rows = [
            tuple(_prepare_value(row.get(col)) for col in columns)
            for row in rows
        ]
        
        await conn.executemany(query, prepared_rows)
        return len(rows)


async def transaction_context():
    """
    Context manager for database transactions.
    
    Example:
        async with transaction_context() as conn:
            await conn.execute("INSERT INTO people ...")
            await conn.execute("INSERT INTO assignments ...")
            # Commits on success, rolls back on exception
    """
    async with get_connection() as conn:
        async with conn.transaction():
            yield conn

# Helper method that takes a Python dictionary and converts all values to PostgreSQL-compatible types.
# Python dictionaries and lists can't be inserted directly into PostgreSQL JSONB columns. They need to be JSON strings.
def _prepare_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare data for PostgreSQL insertion."""
    return {k: _prepare_value(v) for k, v in data.items()}

def _prepare_value(value: Any) -> Any:
    """Convert Python values to PostgreSQL-compatible types."""
    if isinstance(value, (dict, list)):
        # Convert dicts/lists to JSON strings for JSONB columns
        return json.dumps(value)
    return value


# Audit logging helper
async def log_function_call(
    function_name: str,
    params: Dict[str, Any],
    result: Any = None,
    workflow_run_id: Optional[str] = None,
    user_id: Optional[str] = None,
    duration_ms: Optional[int] = None,
    error: Optional[str] = None
):
    """
    Log a function call to the audit_log table.
    
    Example:
        await log_function_call(
            "load_data",
            {"csv_url": "volunteers.csv", "entity_type": "Person"},
            result={"rows_loaded": 50},
            workflow_run_id=workflow_id
        )
    """
    await insert_one("audit_log", {
        "function_name": function_name,
        "params": params,
        "result": result,
        "workflow_run_id": workflow_run_id,
        "user_id": user_id,
        "duration_ms": duration_ms,
        "error": error
    })

