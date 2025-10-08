"""
./orchestrator/src/graph.py
Main Orchestration Graph - Classifier → Multi-Agent Debate → Executor
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, END, START

from .nodes.classifier import classify_template
from .nodes.debate.orchestrator import (
    initialize_debate_state,
    advance_to_round_2,
    advance_to_round_3
)
from .nodes.debate.agent import execute_agent_action
from .nodes.debate.voting import tally_votes_and_determine_winner
from .nodes.debate.extract_params import extract_params_from_winner
from .nodes.debate import get_agent_configs


# ============================================================================
# DEBATE ROUND EXECUTION NODES
# ============================================================================

def execute_round_1(state: Dict[str, Any]) -> Dict[str, Any]:
    """Execute Round 1: All agents propose"""
    agents = get_agent_configs()
    
    print("\n" + "="*80)
    print("📝 ROUND 1: PROPOSALS")
    print("="*80)
    
    for agent in agents:
        state = execute_agent_action(agent.name, state)
    
    return state


def execute_round_2(state: Dict[str, Any]) -> Dict[str, Any]:
    """Execute Round 2: All agents rebut"""
    agents = get_agent_configs()
    
    print("\n" + "="*80)
    print("💬 ROUND 2: REBUTTALS")
    print("="*80)
    
    for agent in agents:
        state = execute_agent_action(agent.name, state)
    
    return state


def execute_round_3(state: Dict[str, Any]) -> Dict[str, Any]:
    """Execute Round 3: All agents vote"""
    agents = get_agent_configs()
    
    print("\n" + "="*80)
    print("🗳️  ROUND 3: VOTING")
    print("="*80)
    
    for agent in agents:
        state = execute_agent_action(agent.name, state)
    
    return state


# ============================================================================
# BUILD MAIN ORCHESTRATOR GRAPH
# ============================================================================

def create_orchestrator_graph():
    """
    Create the main orchestration graph.
    
    Flow:
    START → classifier → initialize_debate → round_1 → advance_2 → round_2 
          → advance_3 → round_3 → tally_votes → extract_params → END
    
    Future: Add executor node after extract_params
    """
    
    graph = StateGraph(dict)
    
    # Add all nodes
    graph.add_node("classifier", classify_template)
    graph.add_node("initialize_debate", initialize_debate_state)
    graph.add_node("round_1_proposals", execute_round_1)
    graph.add_node("advance_to_round_2", advance_to_round_2)
    graph.add_node("round_2_rebuttals", execute_round_2)
    graph.add_node("advance_to_round_3", advance_to_round_3)
    graph.add_node("round_3_voting", execute_round_3)
    graph.add_node("tally_votes", tally_votes_and_determine_winner)
    graph.add_node("extract_params", extract_params_from_winner)
    
    # Define linear flow
    graph.add_edge(START, "classifier")
    graph.add_edge("classifier", "initialize_debate")
    graph.add_edge("initialize_debate", "round_1_proposals")
    graph.add_edge("round_1_proposals", "advance_to_round_2")
    graph.add_edge("advance_to_round_2", "round_2_rebuttals")
    graph.add_edge("round_2_rebuttals", "advance_to_round_3")
    graph.add_edge("advance_to_round_3", "round_3_voting")
    graph.add_edge("round_3_voting", "tally_votes")
    graph.add_edge("tally_votes", "extract_params")
    graph.add_edge("extract_params", END)
    
    # TODO: Add executor node after extract_params
    # graph.add_edge("extract_params", "executor")
    # graph.add_edge("executor", END)
    
    return graph.compile()


# ============================================================================
# CONVENIENCE WRAPPER
# ============================================================================

async def run_orchestration(request: str, available_files: list = None) -> Dict[str, Any]:
    """
    Convenience wrapper to run full orchestration.
    
    Args:
        request: Natural language request
        available_files: List of CSV filenames available (optional)
        
    Returns:
        Final state with approval_id, debate_history, params, etc.
    """
    graph = create_orchestrator_graph()
    
    initial_state = {
        'request': request,
        'available_files': available_files or [],
        'agent_initiated': False,
        'errors': [],
        'clarifications': []
    }
    
    result = await graph.ainvoke(initial_state)
    
    return result