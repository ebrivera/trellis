"""
./orchestrator/src/graph.py
Main Orchestration Graph - Classifier → Multi-Agent Debate → Executor
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, END, START
from typing import Dict, Any
import json
from uuid import uuid4

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
from .graph_executor import generate_preview
from .database import insert_one, execute as db_execute
from decimal import Decimal


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
# ADD APPROVAL GATE CREATION
# ============================================================================

async def create_approval_gate_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create workflow_run and approval_gate in database.
    Generates preview of what will happen.
    Returns approval_id for frontend.
    """
    workflow_id = str(uuid4())
    approval_id = str(uuid4())
    
    debate_state = state['debate_state']
    params = debate_state['params']
    template = state['template']
    
    # Create workflow_run
    await insert_one("workflow_runs", {
        "id": workflow_id,
        "template_type": template.value,
        "status": "awaiting_approval",
        "request_text": state['request'],
        "extracted_params": json.dumps(params)
    })
    
    # Generate preview (dry-run execution)
    preview = await generate_preview(template, params, workflow_id)

    # Helper to serialize preview with Decimal handling
    def serialize_for_json(obj):
        """Convert Decimal and other non-serializable types to JSON-safe values"""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: serialize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [serialize_for_json(item) for item in obj]
        return obj

    preview_serialized = serialize_for_json(preview)

    # Create approval_gate
    await insert_one("approval_gates", {
        "id": approval_id,
        "workflow_run_id": workflow_id,
        "gate_type": "assignments",
        "status": "pending",
        "preview_data": json.dumps(preview_serialized),
        "metrics": json.dumps({
            "debate_vote_tally": debate_state['vote_tally'],
            "winning_agent": debate_state['winning_agent']
        })
    })
    
    # Add to state for API response
    state['approval_id'] = approval_id
    state['workflow_id'] = workflow_id
    state['preview'] = preview
    
    print("\n" + "="*80)
    print("✅ APPROVAL GATE CREATED")
    print("="*80)
    print(f"Approval ID: {approval_id}")
    print(f"Workflow ID: {workflow_id}")

    # Better preview display
    if 'proposed_assignments' in preview:
        print(f"Preview: {preview['proposed_assignments']} proposed assignments")
    elif 'flagged_count' in preview:
        print(f"Preview: {preview['flagged_count']} flagged entities")
    else:
        print(f"Preview: {preview.get('entities_analyzed', 0)} entities analyzed")

    print("="*80 + "\n")
    
    return state

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def reformat_veto_message(winning_strategy: str) -> str:
    """
    Convert agent's technical veto message into natural, church-appropriate language.

    Removes technical jargon like "ABSOLUTE VETO", "Dim 1", etc.
    Extracts the core concern and reformats in a pastoral tone.
    """
    import re

    # Remove "I invoke ABSOLUTE VETO." prefix
    strategy = re.sub(r'^I invoke ABSOLUTE VETO\.\s*', '', winning_strategy, flags=re.IGNORECASE)

    # Remove dimensional references like "(Dim 1)", "(Dim 7)", etc.
    strategy = re.sub(r'\(Dim\s+\d+\)', '', strategy)

    # Remove "by using" or similar connector phrases that make it sound like a list
    strategy = re.sub(r'\s+by (using|promoting|creating)\s+', ', which would ', strategy)

    # Clean up extra whitespace
    strategy = re.sub(r'\s+', ' ', strategy).strip()

    # Add a more pastoral opening if the message is about relationships/ethics
    if any(keyword in strategy.lower() for keyword in ['violates', 'transactional', 'pressure', 'judgment']):
        # Extract the core concern (usually the first sentence or clause)
        first_sentence = strategy.split('.')[0] if '.' in strategy else strategy
        rest = '.'.join(strategy.split('.')[1:]).strip() if '.' in strategy else ''

        # Reconstruct with gentler framing
        if rest:
            return f"After careful consideration, we have some concerns about this approach.\n\n{first_sentence}. {rest}\n\nLet's explore a different approach that better aligns with our values of authentic relationships and genuine care for people."
        else:
            return f"After careful consideration, we have some concerns about this approach.\n\n{first_sentence}.\n\nLet's explore a different approach that better aligns with our values of authentic relationships and genuine care for people."

    return strategy


# ============================================================================
# CONDITIONAL ROUTING FUNCTIONS
# ============================================================================

def should_continue_after_classifier(state: Dict[str, Any]) -> str:
    """
    Determine if we should continue to debate or stop for clarification.

    Returns:
        "needs_clarification" if confidence < 0.8 and clarifying question exists
        "continue_to_debate" if confidence >= 0.8 or no clarification needed
    """
    clarifications = state.get('clarifications', [])
    confidence = state.get('confidence', 1.0)

    if clarifications and confidence < 0.8:
        print("\n" + "="*80)
        print("⚠️  LOW CONFIDENCE - CLARIFICATION NEEDED")
        print("="*80)
        print(f"Confidence: {confidence:.2f} (threshold: 0.80)")
        print(f"Question: {clarifications[0]}")
        print("="*80 + "\n")
        return "needs_clarification"

    return "continue_to_debate"


def should_continue_after_veto(state: Dict[str, Any]) -> str:
    """
    Determine if we should continue to extraction or halt for ethical concerns.

    NEW BEHAVIOR: Both total and partial rejections now halt execution and return
    clarification to the user, but with different messaging:

    - TOTAL REJECTION: Entire request is unethical → explain concerns, ask to rephrase
    - PARTIAL REJECTION: Specific filters are unethical → explain concerns, present
      sanitized alternative, ask if it achieves their goal

    Returns:
        "ethical_veto" if any veto detected (halt execution)
        "continue_to_extraction" if no veto
    """
    debate_state = state.get('debate_state', {})
    veto_override = debate_state.get('veto_override', False)

    if not veto_override:
        # No veto detected, continue normally
        return "continue_to_extraction"

    # Veto detected - halt and generate appropriate clarification message
    winning_agent = debate_state.get('winning_agent', 'HumanFlourishing')
    winning_strategy = debate_state.get('winning_strategy', '')
    veto_type = debate_state.get('veto_type')

    # Reformat the technical veto message into natural language
    natural_message = reformat_veto_message(winning_strategy)

    if veto_type == 'total_rejection':
        # Entire request is unethical
        state['clarifications'] = [
            f"💜 We'd Like to Suggest a Different Approach\n\n"
            f"{natural_message}\n\n"
            "What would you like to do? Feel free to rephrase your request, or let us know more about what you're hoping to accomplish."
        ]

        print("\n" + "="*80)
        print("🚫 TOTAL REJECTION - HALTING WORKFLOW")
        print("="*80)
        print(f"Reason: Entire request violates ethical principles")
        print(f"Action: Returning concerns to user for rephrasing")
        print("="*80 + "\n")

    elif veto_type == 'partial_rejection':
        # Specific filters are unethical, but core request is okay
        state['clarifications'] = [
            f"💜 We'd Like to Suggest a Different Approach\n\n"
            f"{natural_message}\n\n"
            "What would you like to do? If this alternative sounds good, please rephrase your request. Or, let us know more about what you're hoping to accomplish and we can explore other options together."
        ]

        print("\n" + "="*80)
        print("✏️  PARTIAL REJECTION - HALTING FOR USER CONFIRMATION")
        print("="*80)
        print(f"Reason: Specific filters violate ethical principles")
        print(f"Action: Presenting sanitized alternative to user")
        print("="*80 + "\n")

    return "ethical_veto"


# ============================================================================
# BUILD MAIN ORCHESTRATOR GRAPH
# ============================================================================

def create_orchestrator_graph():
    """
    Create the main orchestration graph.

    Flow:
    START → classifier → [CONDITIONAL 1]
                         ├─ needs_clarification → END (return question to user)
                         └─ continue_to_debate → initialize_debate → round_1 → advance_2 → round_2
                                                → advance_3 → round_3 → tally_votes → [CONDITIONAL 2]
                                                                                      ├─ total_rejection → END (ethical veto)
                                                                                      └─ continue_to_extraction → extract_params
                                                                                                                → create_approval_gate → END
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
    graph.add_node("create_approval_gate", create_approval_gate_node)

    # Define flow
    graph.add_edge(START, "classifier")

    # CONDITIONAL: Check if clarification is needed after classification
    graph.add_conditional_edges(
        "classifier",
        should_continue_after_classifier,
        {
            "needs_clarification": END,  # Stop and return clarifications to user
            "continue_to_debate": "initialize_debate"  # Continue to debate
        }
    )
    graph.add_edge("initialize_debate", "round_1_proposals")
    graph.add_edge("round_1_proposals", "advance_to_round_2")
    graph.add_edge("advance_to_round_2", "round_2_rebuttals")
    graph.add_edge("round_2_rebuttals", "advance_to_round_3")
    graph.add_edge("advance_to_round_3", "round_3_voting")
    graph.add_edge("round_3_voting", "tally_votes")

    # CONDITIONAL: Check if ethical veto requires halting execution
    graph.add_conditional_edges(
        "tally_votes",
        should_continue_after_veto,
        {
            "ethical_veto": END,  # Stop and return ethical concerns/alternative to user
            "continue_to_extraction": "extract_params"  # Continue to parameter extraction
        }
    )

    graph.add_edge("extract_params", "create_approval_gate")
    graph.add_edge("create_approval_gate", END)
    
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