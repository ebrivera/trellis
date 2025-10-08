"""
Test individual agent logic before wiring into graph
"""

import asyncio
import os
from dotenv import load_dotenv
from src.schemas import TemplateType
from src.nodes.debate.orchestrator import initialize_debate_state
from src.nodes.debate.agent import agent_propose, agent_rebut, agent_vote
from src.nodes.debate import get_agent_configs

load_dotenv()

def test_agent_proposal():
    """Test Round 1: Agent proposals"""
    print("\n" + "="*80)
    print("TEST 1: AGENT PROPOSALS (Round 1)")
    print("="*80)
    
    # Initialize state
    state = {
        'request': "Match volunteers to Sunday morning roles based on skills and availability",
        'template': TemplateType.MATCHING,
        'agent_initiated': False
    }
    state = initialize_debate_state(state)
    
    # Each agent proposes
    agents = get_agent_configs()
    for agent in agents:
        state = agent_propose(agent.name, state)
    
    # Verify proposals were added
    debate_state = state['debate_state']
    assert len(debate_state['proposals']) == 3, "Should have 3 proposals"
    assert len(debate_state['debate_history']) == 3, "Should have 3 history entries"
    
    print("\n✅ All agents proposed successfully!")
    print(f"\nProposals collected:")
    for agent_name, proposal in debate_state['proposals'].items():
        print(f"  - {agent_name}: {proposal[:60]}...")
    
    return state


def test_agent_rebuttal(state):
    """Test Round 2: Agent rebuttals"""
    print("\n" + "="*80)
    print("TEST 2: AGENT REBUTTALS (Round 2)")
    print("="*80)
    
    # Advance to round 2
    from src.nodes.debate.orchestrator import advance_to_round_2
    state = advance_to_round_2(state)
    
    # Each agent rebuts
    agents = get_agent_configs()
    for agent in agents:
        state = agent_rebut(agent.name, state)
    
    # Verify rebuttals were added
    debate_state = state['debate_state']
    assert len(debate_state['rebuttals']) == 3, "Should have 3 rebuttals"
    assert len(debate_state['debate_history']) == 6, "Should have 6 total history entries (3 proposals + 3 rebuttals)"
    
    print("\n✅ All agents rebutted successfully!")
    print(f"\nRebuttals collected:")
    for agent_name, rebuttal in debate_state['rebuttals'].items():
        print(f"  - {agent_name}: {rebuttal[:60]}...")
    
    return state


def test_agent_voting(state):
    """Test Round 3: Agent voting + tie-breaking"""
    print("\n" + "="*80)
    print("TEST 3: AGENT VOTING (Round 3)")
    print("="*80)
    
    # Advance to round 3
    from src.nodes.debate.orchestrator import advance_to_round_3
    state = advance_to_round_3(state)
    
    # Each agent votes
    agents = get_agent_configs()
    for agent in agents:
        state = agent_vote(agent.name, state)
    
    # Verify votes were added
    debate_state = state['debate_state']
    assert len(debate_state['votes']) == 3, "Should have 3 votes"
    
    print("\n✅ All agents voted successfully!")
    
    # Tally votes and determine winner (with tie-breaking if needed)
    from src.nodes.debate.voting import tally_votes_and_determine_winner
    state = tally_votes_and_determine_winner(state)
    
    debate_state = state['debate_state']
    
    print(f"\n🏆 Final Winner: {debate_state['winning_agent']}")
    if debate_state.get('tie_broken_by_moderator'):
        print(f"   (Tie broken by Moderator)")
        print(f"   Justification: {debate_state['moderator_decision']['justification']}")
    else:
        print(f"   Vote tally: {debate_state['vote_tally']}")
    
    return state


def test_moderator_tiebreaker():
    """Test moderator tie-breaking by forcing a 1-1-1 tie"""
    print("\n" + "="*80)
    print("TEST 4: MODERATOR TIE-BREAKER (Forced Tie)")
    print("="*80)
    
    # Initialize state
    state = {
        'request': "Match volunteers to Sunday morning roles based on skills and availability",
        'template': TemplateType.MATCHING,
        'agent_initiated': False
    }
    state = initialize_debate_state(state)
    
    # Manually create proposals (simulate Round 1)
    debate_state = state['debate_state']
    debate_state['proposals'] = {
        'Planner': 'Use capacity-balanced matching with skills as primary criterion and availability as secondary.',
        'Operations': 'Use conservative matching with 10% over-scheduling buffer to prevent last-minute gaps.',
        'HumanFlourishing': 'Use relational matching prioritizing spiritual gifts and community connections over efficiency.'
    }
    debate_state['debate_history'] = [
        {"round": 1, "agent": "Planner", "message_type": "proposal", "content": debate_state['proposals']['Planner']},
        {"round": 1, "agent": "Operations", "message_type": "proposal", "content": debate_state['proposals']['Operations']},
        {"round": 1, "agent": "HumanFlourishing", "message_type": "proposal", "content": debate_state['proposals']['HumanFlourishing']},
    ]
    
    # Manually create rebuttals (simulate Round 2)
    debate_state['rebuttals'] = {
        'Planner': 'Operations proposal is too conservative, HumanFlourishing is too idealistic.',
        'Operations': 'Planner risks under-scheduling, HumanFlourishing ignores logistical constraints.',
        'HumanFlourishing': 'Both proposals treat people as resources rather than souls with unique callings.'
    }
    debate_state['debate_history'].extend([
        {"round": 2, "agent": "Planner", "message_type": "rebuttal", "content": debate_state['rebuttals']['Planner']},
        {"round": 2, "agent": "Operations", "message_type": "rebuttal", "content": debate_state['rebuttals']['Operations']},
        {"round": 2, "agent": "HumanFlourishing", "message_type": "rebuttal", "content": debate_state['rebuttals']['HumanFlourishing']},
    ])
    
    # FORCE A TIE: Each agent votes for a different agent (1-1-1 tie)
    print("\n🎲 Forcing a 1-1-1 tie scenario...")
    debate_state['current_round'] = 3
    debate_state['votes'] = {
        'Planner': 'Operations',
        'Operations': 'HumanFlourishing',
        'HumanFlourishing': 'Planner'
    }
    debate_state['debate_history'].extend([
        {"round": 3, "agent": "Planner", "message_type": "vote", "content": "Operations"},
        {"round": 3, "agent": "Operations", "message_type": "vote", "content": "HumanFlourishing"},
        {"round": 3, "agent": "HumanFlourishing", "message_type": "vote", "content": "Planner"},
    ])
    
    print(f"   Planner voted for: Operations")
    print(f"   Operations voted for: HumanFlourishing")
    print(f"   HumanFlourishing voted for: Planner")
    print(f"   Result: 1-1-1 TIE\n")
    
    # Verify tie detection works
    from src.nodes.debate.tiebreaker import check_for_tie
    assert check_for_tie(debate_state), "Tie should be detected!"
    
    # Tally votes - should invoke moderator
    from src.nodes.debate.voting import tally_votes_and_determine_winner
    state = tally_votes_and_determine_winner(state)
    
    debate_state = state['debate_state']
    
    # Verify moderator was invoked
    assert debate_state.get('tie_broken_by_moderator') == True, "Moderator should have been invoked!"
    assert debate_state.get('moderator_decision') is not None, "Moderator decision should exist!"
    assert debate_state['winning_agent'] is not None, "Should have a winner after tie-breaking!"
    
    print(f"\n✅ Moderator successfully broke the tie!")
    print(f"   Winner: {debate_state['winning_agent']}")
    print(f"   Justification: {debate_state['moderator_decision']['justification']}")
    
    # Check that moderator decision was added to history
    moderator_entries = [e for e in debate_state['debate_history'] if e.get('agent') == 'Moderator']
    assert len(moderator_entries) == 1, "Should have exactly one moderator entry in history"
    assert moderator_entries[0]['message_type'] == 'tiebreaker', "Moderator entry should be tiebreaker type"
    
    print(f"\n✅ All tie-breaker assertions passed!")
    
    return state

if __name__ == "__main__":
    print("="*80)
    print("TESTING AGENT LOGIC IN ISOLATION")
    print("="*80)
    
    # Run normal debate tests
    state = test_agent_proposal()
    state = test_agent_rebuttal(state)
    state = test_agent_voting(state)
    
    # Run dedicated tie-breaker test
    state_tie = test_moderator_tiebreaker()
    
    print("\n" + "="*80)
    print("✅ ALL AGENT LOGIC TESTS PASSED (INCLUDING TIE-BREAKER)")
    print("="*80)
    print("\nNormal debate history:")
    for entry in state['debate_state']['debate_history']:
        print(f"  Round {entry['round']} - {entry['agent']} ({entry['message_type']}): {entry['content'][:50]}...")
    
    print("\nTie-breaker debate history:")
    for entry in state_tie['debate_state']['debate_history']:
        print(f"  Round {entry['round']} - {entry['agent']} ({entry['message_type']}): {entry['content'][:50]}...")