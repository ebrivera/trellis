# test_debate_graph.py

import asyncio
from dotenv import load_dotenv
from src.schemas import TemplateType
from src.graph import create_orchestrator_graph
from src.database import init_db_pool, close_db_pool

load_dotenv()


async def test_full_orchestration():
    """Test complete flow: classifier → debate → extract params → approval gate"""
    
    # Initialize database
    await init_db_pool()
    
    print("="*80)
    print("TESTING COMPLETE ORCHESTRATOR GRAPH")
    print("="*80)
    
    # Create the main orchestrator graph
    orchestrator = create_orchestrator_graph()
    
    # Initial state (just the request)
    initial_state = {
        'request': "Match volunteers to Sunday morning serving roles based on their skills and availability",
        'agent_initiated': False
    }
    
    # Run the full graph
    print("\n🚀 Starting orchestrator execution...\n")
    final_state = await orchestrator.ainvoke(initial_state)
    
    # Validate results
    print("\n" + "="*80)
    print("VALIDATION")
    print("="*80)
    
    # Check classifier worked
    assert final_state['template'] is not None, "Should have classified template"
    assert final_state['template'] == TemplateType.MATCHING, "Should be matching template"
    print(f"✓ Classifier worked: {final_state['template'].value}")
    
    # Check debate completed
    debate_state = final_state['debate_state']
    assert len(debate_state['proposals']) == 3, "Should have 3 proposals"
    assert len(debate_state['rebuttals']) == 3, "Should have 3 rebuttals"
    assert len(debate_state['votes']) == 3, "Should have 3 votes"
    print("✓ All 3 debate rounds completed")
    
    # Check winner determined
    assert debate_state['winning_agent'] is not None, "Should have a winner"
    assert debate_state['winning_strategy'] is not None, "Should have winning strategy"
    print(f"✓ Winner determined: {debate_state['winning_agent']}")
    
    # Check params extracted
    assert final_state['params'] is not None, "Should have extracted params"
    assert 'source' in final_state['params'], "Params should have source"
    assert 'target' in final_state['params'], "Params should have target"
    print("✓ Parameters extracted")
    
    # Check approval gate created
    assert 'approval_id' in final_state, "Should have approval_id"
    assert 'workflow_id' in final_state, "Should have workflow_id"
    assert 'preview' in final_state, "Should have preview"
    print(f"✓ Approval gate created: {final_state['approval_id']}")
    print(f"  Preview: {final_state['preview'].get('proposed_assignments', 0)} assignments")
    
    # Print summary
    print("\n" + "="*80)
    print("ORCHESTRATION SUMMARY")
    print("="*80)
    print(f"Request: {final_state['request']}")
    print(f"Template: {final_state['template'].value}")
    print(f"Confidence: {final_state.get('confidence', 'N/A')}")
    
    print(f"\n🎭 Debate Results:")
    print(f"  Winner: {debate_state['winning_agent']}")
    print(f"  Vote tally: {debate_state['vote_tally']}")
    print(f"\n  Winning strategy:")
    print(f"    {debate_state['winning_strategy'][:150]}...")
    
    print(f"\n🔧 Extracted Parameters:")
    print(f"  Source: {final_state['params']['source']['entity_type']}")
    print(f"  Target: {final_state['params']['target']['entity_type']}")
    print(f"  Strategy: {final_state['params']['match_strategy']}")
    
    print(f"\n📋 Approval Gate:")
    print(f"  ID: {final_state['approval_id']}")
    print(f"  Workflow ID: {final_state['workflow_id']}")
    print(f"  Proposed assignments: {final_state['preview'].get('proposed_assignments', 0)}")
    print(f"  Match rate: {final_state['preview'].get('match_rate', 0)}")
    
    print("\n" + "="*80)
    print("✅ COMPLETE ORCHESTRATOR TEST PASSED")
    print("="*80)
    
    # Close database
    await close_db_pool()

asyncio.run(test_full_orchestration())