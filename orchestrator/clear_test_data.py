# orchestrator/clear_test_data.py

import asyncio
from dotenv import load_dotenv
load_dotenv()

from src.database import init_db_pool, execute, close_db_pool  # Changed here

async def clear_test_data():
    await init_db_pool()
    
    print("Clearing test data...")
    await execute("TRUNCATE TABLE approval_gates CASCADE")  # And here
    await execute("TRUNCATE TABLE workflow_runs CASCADE")
    await execute("TRUNCATE TABLE assignments CASCADE")
    await execute("TRUNCATE TABLE messages CASCADE")
    
    print("✓ All test tables cleared!")
    print("✓ People and groups preserved")
    
    await close_db_pool()

asyncio.run(clear_test_data())