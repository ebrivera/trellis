"""
./orchestrator/src/nodes/debate/voting.py
Voting Node - Tallies votes and determines winner (with tie-breaking)
"""

from typing import Dict, Any
from .tiebreaker import check_for_tie, moderator_breaks_tie


def tally_votes_and_determine_winner(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Count votes and determine debate winner.
    If there's a tie, invoke moderator to break it.
    
    Args:
        state: Orchestrator state with completed voting
        
    Returns:
        Updated state with winning_agent, winning_strategy, vote_tally
    """
    debate_state = state['debate_state']
    
    # Count votes
    vote_counts = {}
    for voted_for in debate_state['votes'].values():
        vote_counts[voted_for] = vote_counts.get(voted_for, 0) + 1
    
    print("\n" + "="*80)
    print("🗳️  VOTE TALLYING")
    print("="*80)
    print(f"Votes cast: {debate_state['votes']}")
    print(f"Vote tally: {vote_counts}")
    
    # Check for tie
    if check_for_tie(debate_state):
        print("\n⚠️  TIE DETECTED - Invoking moderator...")
        state = moderator_breaks_tie(state)
        debate_state = state['debate_state']  # Refresh after moderator update
    else:
        # Normal case: clear winner
        winner_name = max(vote_counts, key=vote_counts.get)
        winning_proposal = debate_state['proposals'][winner_name]
        
        debate_state['winning_agent'] = winner_name
        debate_state['winning_strategy'] = winning_proposal
        debate_state['vote_tally'] = vote_counts
        debate_state['tie_broken_by_moderator'] = False
        
        print(f"\n🏆 Winner: {winner_name} ({vote_counts[winner_name]}/{len(debate_state['votes'])} votes)")
    
    print("="*80 + "\n")
    
    return state