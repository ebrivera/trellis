import asyncio
from dotenv import load_dotenv
load_dotenv()

from src.graph import orchestrate_request
from src.database import init_db_pool, close_db_pool

async def test_orchestration():
    await init_db_pool()
    
    print("Testing full orchestration pipeline...")
    print("=" * 60)
    
    result = await orchestrate_request(
        "Match mentors to mentees based on interests and availability"
    )
    
    print(f"✓ Orchestration complete!")
    print(f"  Approval ID: {result['approval_id']}")
    print(f"  Workflow ID: {result['workflow_id']}")
    print(f"  Template: {result['template']}")
    print(f"  Preview keys: {list(result['preview'].keys())}")
    print(f"  Proposed assignments: {result['preview'].get('proposed_assignments', 'N/A')}")
    print(f"  Match rate: {result['preview'].get('match_rate', 'N/A')}")
    
    await close_db_pool()

asyncio.run(test_orchestration())
