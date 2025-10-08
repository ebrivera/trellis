"""
./orchestrator/src/nodes/debate/tiebreaker.py
Tie-Breaker Logic - Moderator agent resolves voting deadlocks
"""

import os
from openai import OpenAI
from typing import Dict, Any
from . import get_moderator_config, load_persona
from .orchestrator import format_debate_history_for_voting

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def check_for_tie(debate_state: Dict[str, Any]) -> bool:
    """
    Check if voting resulted in a tie.
    
    Returns:
        True if all agents have equal votes (e.g., 1-1-1 or 2-2-2)
    """
    votes = debate_state['votes']
    
    # Count votes for each agent
    vote_counts = {}
    for voted_for in votes.values():
        vote_counts[voted_for] = vote_counts.get(voted_for, 0) + 1
    
    # Check if all vote counts are equal
    counts = list(vote_counts.values())
    is_tie = len(set(counts)) == 1 and len(counts) > 1
    
    return is_tie


def moderator_breaks_tie(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Moderator agent breaks a voting tie by evaluating the full debate.
    
    Args:
        state: Current orchestrator state with tied votes
        
    Returns:
        Updated state with moderator's decision as the winner
    """
    debate_state = state['debate_state']
    
    moderator = get_moderator_config()
    persona = load_persona(moderator.persona_file)
    
    print("\n" + "="*80)
    print(f"⚖️  TIE DETECTED - Moderator Breaking Deadlock")
    print("="*80)
    
    # Show current vote tally
    vote_counts = {}
    for voted_for in debate_state['votes'].values():
        vote_counts[voted_for] = vote_counts.get(voted_for, 0) + 1
    
    print(f"Current vote tally: {vote_counts}")
    print("Moderator is reviewing the debate...\n")
    
    # Format complete debate for moderator
    history_text = format_debate_history_for_voting(debate_state)
    
    # Get agent names that received votes (candidates)
    candidates = list(vote_counts.keys())
    
    # Build moderator prompt
    prompt = f"""The debate agents have reached a voting deadlock. You must break the tie.

{history_text}

CURRENT VOTE TALLY (TIE):
{', '.join([f'{agent}: {count} vote(s)' for agent, count in vote_counts.items()])}

Your task: Objectively evaluate all proposals and choose the BEST strategy for this church.

Consider:
- Which proposal demonstrates the strongest reasoning?
- Which approach balances all important concerns (efficiency, feasibility, human flourishing)?
- Which strategy has the highest likelihood of success?
- Are there any proposals that synthesize multiple perspectives effectively?

You must choose from: {', '.join(candidates)}

Respond with TWO lines:
Line 1: The agent name you're selecting as the winner
Line 2: A brief justification (one sentence) for why their proposal is best

Example format:
Planner
Their approach balances capacity optimization with practical execution constraints.

Your decision:"""
    
    # Call moderator LLM
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": persona},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,  # Low temperature for consistent decision-making
        max_tokens=100
    )
    
    response_text = response.choices[0].message.content.strip()
    lines = response_text.split('\n')
    
    # Parse moderator decision
    winner = lines[0].strip()
    justification = lines[1].strip() if len(lines) > 1 else "Moderator selected based on overall merit."
    
    # Validate winner is one of the candidates
    if winner not in candidates:
        # Try to find the name in the response
        for candidate in candidates:
            if candidate.lower() in winner.lower():
                winner = candidate
                break
        else:
            # Fallback to first candidate
            print(f"  ⚠️  Could not parse moderator decision '{winner}', defaulting to {candidates[0]}")
            winner = candidates[0]
    
    print(f"\n{moderator.emoji} {moderator.name} decision: {winner}")
    print(f"   Justification: {justification}")
    
    # Update debate state with moderator decision
    debate_state['moderator_decision'] = {
        'winner': winner,
        'justification': justification
    }
    debate_state['winning_agent'] = winner
    debate_state['winning_strategy'] = debate_state['proposals'][winner]
    debate_state['vote_tally'] = vote_counts
    debate_state['tie_broken_by_moderator'] = True
    
    # Add moderator decision to debate history
    debate_state['debate_history'].append({
        "round": 4,  # Special round for tie-breaker
        "agent": "Moderator",
        "message_type": "tiebreaker",
        "content": f"Selected {winner}. {justification}"
    })
    
    print("="*80 + "\n")
    
    return state