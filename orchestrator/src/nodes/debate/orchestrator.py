"""
Debate Orchestrator - Manages debate state transitions and formatting
"""

from typing import Dict, Any, List
from ...schemas import DebateState, OrchestratorState
from . import get_agent_configs


def initialize_debate_state(orchestrator_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert orchestrator state into debate-ready state for Round 1.
    This is called at the start of debate flow.
    
    Args:
        orchestrator_state: Dict with 'request', 'template', etc.
        
    Returns:
        Updated state with initialized debate_state nested dict
    """
    debate_state = {
        'request': orchestrator_state['request'],
        'template': orchestrator_state['template'],
        'current_round': 1,
        'proposals': {},
        'rebuttals': {},
        'votes': {},
        'debate_history': [],
        'winning_agent': None,
        'winning_strategy': None,
        'vote_tally': None,
        'params': None,
        'agent_initiated': orchestrator_state.get('agent_initiated', False),
        'errors': []
    }
    
    # Add debate_state as nested dict
    orchestrator_state['debate_state'] = debate_state
    
    print("\n" + "="*80)
    print("🎭 INITIALIZING MULTI-AGENT DEBATE")
    print("="*80)
    print(f"Request: {orchestrator_state['request']}")
    print(f"Template: {orchestrator_state['template']}")
    print(f"Agents: {', '.join([a.name for a in get_agent_configs()])}")
    print("="*80 + "\n")
    
    return orchestrator_state


def advance_to_round_2(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transition from Round 1 (proposals) to Round 2 (rebuttals).
    Called after all agents have proposed.
    """
    debate_state = state['debate_state']
    debate_state['current_round'] = 2
    
    print("\n" + "="*80)
    print(f"📝 ROUND 1 COMPLETE - {len(debate_state['proposals'])} proposals collected")
    print("="*80)
    for agent_name, proposal in debate_state['proposals'].items():
        print(f"\n{agent_name}:")
        print(f"  {proposal[:150]}{'...' if len(proposal) > 150 else ''}")
    print("\n" + "="*80 + "\n")
    
    return state


def advance_to_round_3(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transition from Round 2 (rebuttals) to Round 3 (voting).
    Called after all agents have rebutted.
    """
    debate_state = state['debate_state']
    debate_state['current_round'] = 3
    
    print("\n" + "="*80)
    print(f"💬 ROUND 2 COMPLETE - {len(debate_state['rebuttals'])} rebuttals collected")
    print("="*80)
    for agent_name, rebuttal in debate_state['rebuttals'].items():
        print(f"\n{agent_name}:")
        print(f"  {rebuttal[:150]}{'...' if len(rebuttal) > 150 else ''}")
    print("\n" + "="*80 + "\n")
    
    return state


def format_proposals_for_rebuttal(debate_state: Dict[str, Any], current_agent: str) -> str:
    """
    Format other agents' proposals for rebuttal context.
    Excludes the current agent's own proposal.
    """
    proposals = debate_state['proposals']
    others = {k: v for k, v in proposals.items() if k != current_agent}
    
    lines = []
    for agent_name, proposal in others.items():
        lines.append(f"**{agent_name}'s proposal:**")
        lines.append(f"{proposal}")
        lines.append("")
    
    return "\n".join(lines)


def format_debate_history_for_voting(debate_state: Dict[str, Any]) -> str:
    """
    Format complete debate history for voting context.
    """
    lines = []
    
    lines.append("=" * 70)
    lines.append("COMPLETE DEBATE HISTORY")
    lines.append("=" * 70)
    
    lines.append("\n📝 ROUND 1 - PROPOSALS:\n")
    for agent_name, proposal in debate_state['proposals'].items():
        lines.append(f"{agent_name}:")
        lines.append(f"  {proposal}")
        lines.append("")
    
    lines.append("\n💬 ROUND 2 - REBUTTALS:\n")
    for agent_name, rebuttal in debate_state['rebuttals'].items():
        lines.append(f"{agent_name}:")
        lines.append(f"  {rebuttal}")
        lines.append("")
    
    lines.append("=" * 70)
    
    return "\n".join(lines)


def get_active_agents(state: Dict[str, Any]) -> List[str]:
    """
    Return list of agent names that should participate in current round.
    Used for parallel execution via LangGraph's Send API.
    """
    agents = get_agent_configs()
    return [agent.name for agent in agents]