"""
Test the complete orchestrator graph end-to-end
"""

import asyncio
from dotenv import load_dotenv
from src.schemas import TemplateType
from src.graph import create_orchestrator_graph  # Changed import

load_dotenv()


async def test_full_orchestration():
    """Test complete flow: classifier → debate → extract params"""
    
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
    print(f"✓ Parameters extracted")
    
    # Print summary
    print("\n" + "="*80)
    print("ORCHESTRATION SUMMARY")
    print("="*80)
    print(f"Request: {final_state['request']}")
    print(f"Template: {final_state['template'].value}")
    print(f"Confidence: {final_state['confidence']:.2f}")
    
    print(f"\n🎭 Debate Results:")
    print(f"  Winner: {debate_state['winning_agent']}")
    if debate_state.get('tie_broken_by_moderator'):
        print(f"  (Tie broken by Moderator)")
        print(f"  Justification: {debate_state['moderator_decision']['justification']}")
    else:
        print(f"  Vote tally: {debate_state['vote_tally']}")
    
    print(f"\n  Winning strategy:")
    print(f"    {debate_state['winning_strategy'][:150]}...")
    
    print(f"\n🔧 Extracted Parameters:")
    print(f"  Source: {final_state['params']['source']['entity_type']}")
    if 'target' in final_state['params']:
        print(f"  Target: {final_state['params']['target']['entity_type']}")
    if 'match_strategy' in final_state['params']:
        print(f"  Strategy: {final_state['params']['match_strategy']}")
    
    print("\n" + "="*80)
    print("✅ COMPLETE ORCHESTRATOR TEST PASSED")
    print("="*80)
    
    return final_state


if __name__ == "__main__":
    asyncio.run(test_full_orchestration())