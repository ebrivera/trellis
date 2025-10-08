"""
./orchestrator/src/nodes/debate/agent.py
Agent Logic - Core reasoning for debate participation
Each agent can propose, rebut, and vote independently
"""

import os
from openai import OpenAI
from typing import Dict, Any, Literal
from . import load_persona, get_agent_by_name
from .orchestrator import (
    format_proposals_for_rebuttal,
    format_debate_history_for_voting
)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def agent_propose(agent_name: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent generates a proposal for Round 1.
    
    Args:
        agent_name: Name of the agent (e.g., "Planner")
        state: Current orchestrator state with debate_state nested
        
    Returns:
        Updated state with agent's proposal added to debate_state
    """
    debate_state = state['debate_state']
    request = debate_state['request']
    template = debate_state['template']
    
    # Get agent config
    agent = get_agent_by_name(agent_name)
    persona = load_persona(agent.persona_file)
    
    print(f"\n{agent.emoji} {agent.name} is proposing...")
    
    # Build proposal prompt
    prompt = f"""Request from church staff:
                "{request}"

                Template type: {template}

                Propose your strategy for handling this request. Be specific about:
                - What data sources to use (people, groups, gifts, etc.)
                - How to approach the {template} (matching algorithm, monitoring conditions, analysis metrics)
                - What constraints or priorities matter most from your perspective

                Keep your proposal to 2-4 sentences. Be direct and actionable.
    """
    
    # Call LLM
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": persona},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=250
    )
    
    proposal = response.choices[0].message.content.strip()
    
    # Update debate state
    debate_state['proposals'][agent_name] = proposal
    debate_state['debate_history'].append({
        "round": 1,
        "agent": agent_name,
        "message_type": "proposal",
        "content": proposal
    })
    
    print(f"  ✓ {agent.name} proposed: {proposal[:80]}...")
    
    return state


def agent_rebut(agent_name: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent generates a rebuttal for Round 2.
    
    Args:
        agent_name: Name of the agent
        state: Current orchestrator state
        
    Returns:
        Updated state with agent's rebuttal added
    """
    debate_state = state['debate_state']
    
    # Get agent config
    agent = get_agent_by_name(agent_name)
    persona = load_persona(agent.persona_file)
    
    print(f"\n{agent.emoji} {agent.name} is rebutting...")
    
    # Get this agent's proposal and others' proposals
    own_proposal = debate_state['proposals'][agent_name]
    others_text = format_proposals_for_rebuttal(debate_state, agent_name)
    
    # Build rebuttal prompt
    prompt = f"""Your proposal was:
            "{own_proposal}"

            The other agents proposed:

            {others_text}

            Respond to their proposals. Consider:
            - Do you agree or disagree with their approaches?
            - What are the flaws in their thinking from your perspective?
            - What are the strengths of your approach compared to theirs?
            - Are there valid points in their proposals you should acknowledge?

            Keep your rebuttal to 2-4 sentences. Be constructive but assertive.
    """
    
    # Call LLM
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": persona},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=250
    )
    
    rebuttal = response.choices[0].message.content.strip()
    
    # Update debate state
    debate_state['rebuttals'][agent_name] = rebuttal
    debate_state['debate_history'].append({
        "round": 2,
        "agent": agent_name,
        "message_type": "rebuttal",
        "content": rebuttal
    })
    
    print(f"  ✓ {agent.name} rebutted: {rebuttal[:80]}...")
    
    return state


def agent_vote(agent_name: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent votes for best strategy in Round 3.
    RULE: Cannot vote for self - must choose another agent's proposal.
    
    Args:
        agent_name: Name of the agent
        state: Current orchestrator state
        
    Returns:
        Updated state with agent's vote added
    """
    debate_state = state['debate_state']
    
    # Get agent config
    agent = get_agent_by_name(agent_name)
    persona = load_persona(agent.persona_file)
    
    print(f"\n{agent.emoji} {agent.name} is voting...")
    
    # Format full debate history
    history_text = format_debate_history_for_voting(debate_state)
    
    # Get list of OTHER agents (exclude self)
    from . import get_agent_configs
    all_agents = [a.name for a in get_agent_configs()]
    other_agents = [name for name in all_agents if name != agent_name]
    
    # Build voting prompt
    prompt = f"""Here is the complete debate:

    {history_text}

    Now you must vote for the BEST strategy to serve this church's needs.

    CRITICAL RULE: You CANNOT vote for your own proposal. You must objectively evaluate the other agents' proposals and vote for the one that will produce the best outcome for the church.

    Consider:
    - Which approach will produce the best real-world outcomes?
    - Which strategy is most aligned with the church's mission?
    - Which proposal is most feasible to execute successfully?
    - Are there valid strengths in another agent's approach that outweigh your own?

    You must choose from: {', '.join(other_agents)}

    Be objective. The church's success depends on choosing the best strategy, not defending your own ego.

    Respond with ONLY the agent name you're voting for.

    Your vote:"""
    
    # Call LLM with lower temperature for more consistent voting
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": persona},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,  # Slightly higher than before for some variability
        max_tokens=30
    )
    
    vote_raw = response.choices[0].message.content.strip()
    
    # Normalize vote (extract agent name from response)
    vote = None
    for candidate_name in other_agents:
        if candidate_name.lower() in vote_raw.lower():
            vote = candidate_name
            break
    
    # Fallback: if we can't parse the vote, pick first other agent
    if vote is None:
        print(f"  ⚠️  Could not parse vote '{vote_raw}', defaulting to {other_agents[0]}")
        vote = other_agents[0]
    
    # Ensure vote is NOT self (safety check)
    if vote == agent_name:
        print(f"  ⚠️  Agent tried to vote for self, forcing vote to {other_agents[0]}")
        vote = other_agents[0]
    
    # Update debate state
    debate_state['votes'][agent_name] = vote
    debate_state['debate_history'].append({
        "round": 3,
        "agent": agent_name,
        "message_type": "vote",
        "content": vote
    })
    
    print(f"  ✓ {agent.name} voted for: {vote}")
    
    return state


def execute_agent_action(agent_name: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Route agent to appropriate action based on current round.
    This is the main entry point for each agent node.
    
    Args:
        agent_name: Name of the agent to execute
        state: Current orchestrator state
        
    Returns:
        Updated state after agent's action
    """
    debate_state = state['debate_state']
    current_round = debate_state['current_round']
    
    if current_round == 1:
        return agent_propose(agent_name, state)
    elif current_round == 2:
        return agent_rebut(agent_name, state)
    elif current_round == 3:
        return agent_vote(agent_name, state)
    else:
        raise ValueError(f"Invalid round number: {current_round}")


# ============================================================================
# INDIVIDUAL AGENT NODE FUNCTIONS
# These become separate nodes in LangGraph for parallel execution
# ============================================================================

def planner_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Planner agent node for LangGraph"""
    return execute_agent_action("Planner", state)


def operations_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Operations agent node for LangGraph"""
    return execute_agent_action("Operations", state)


def human_flourishing_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """HumanFlourishing agent node for LangGraph"""
    return execute_agent_action("HumanFlourishing", state)