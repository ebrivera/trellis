"""
Multi-Agent Debate Node - Core Innovation
3 agents debate strategy, vote on best approach, extract params from winner
"""

import os
from pathlib import Path
from openai import OpenAI
from typing import Dict, Any, List
import json

PROJECT_ROOT = Path(__file__).parent.parent.parent
PERSONAS_DIR = PROJECT_ROOT / "prompts" / "agent_personas"

# Agent configurations
AGENTS = [
    {
        "name": "Planner",
        "persona_file": "planner.txt",
        "emoji": "📊"
    },
    {
        "name": "Operations", 
        "persona_file": "operations.txt",
        "emoji": "⚙️"
    },
    {
        "name": "HumanFlourishing",  # Or whatever you named your third agent
        "persona_file": "human_flourishing.txt",  # Update this filename if you renamed it
        "emoji": "🌱"
    }
]


def load_persona(filename: str) -> str:
    """Load agent persona prompt from file"""
    persona_path = PERSONAS_DIR / filename
    if not persona_path.exists():
        raise FileNotFoundError(f"Persona file not found: {persona_path}")
    return persona_path.read_text()


async def multi_agent_debate(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orchestrate 3-agent debate on request strategy.
    
    Protocol:
    1. Each agent proposes a strategy (Round 1)
    2. Each agent rebuts others' proposals (Round 2)  
    3. Each agent votes for best approach (Round 3)
    4. Extract params from winning strategy
    
    Args:
        state: Must contain 'request' and 'template'
        
    Returns:
        state with added keys:
        - debate_history: List of all agent statements
        - winning_agent: Name of agent whose strategy won
        - winning_strategy: Text of winning proposal
        - vote_tally: Dict of vote counts
        - params: Structured params extracted from winner
    """
    request = state['request']
    template = state['template']
    
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    debate_history = []
    proposals = {}
    
    print("\n" + "="*80)
    print("🎭 MULTI-AGENT DEBATE STARTING")
    print("="*80)
    print(f"Request: {request}")
    print(f"Template: {template.value}")
    print()
    
    # ============================================================
    # ROUND 1: Each agent proposes their strategy
    # ============================================================
    print("📝 ROUND 1: PROPOSALS")
    print("-" * 80)
    
    for agent in AGENTS:
        persona = load_persona(agent['persona_file'])
        
        prompt = f"""Request from church staff:
"{request}"

Propose your strategy for handling this request. Be specific about:
- What data sources to use
- How to approach the matching/monitoring/analysis
- What constraints or priorities matter most

Keep your proposal to 2-3 sentences. Be direct and actionable."""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": persona},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )
        
        proposal = response.choices[0].message.content.strip()
        proposals[agent['name']] = proposal
        
        debate_history.append({
            "round": 1,
            "agent": agent['name'],
            "type": "proposal",
            "content": proposal
        })
        
        print(f"{agent['emoji']} {agent['name']}: {proposal}\n")
    
    # ============================================================
    # ROUND 2: Each agent rebuts others' proposals
    # ============================================================
    print("\n💬 ROUND 2: REBUTTALS")
    print("-" * 80)
    
    for agent in AGENTS:
        persona = load_persona(agent['persona_file'])
        
        # Show this agent what others proposed
        others = {k: v for k, v in proposals.items() if k != agent['name']}
        others_text = "\n\n".join([f"{name}'s proposal:\n{prop}" for name, prop in others.items()])
        
        prompt = f"""Your proposal was:
"{proposals[agent['name']]}"

The other agents proposed:

{others_text}

Respond to their proposals. Do you agree? Disagree? What are the flaws in their thinking? What are the strengths of your approach compared to theirs?

Keep your rebuttal to 2-3 sentences."""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": persona},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )
        
        rebuttal = response.choices[0].message.content.strip()
        
        debate_history.append({
            "round": 2,
            "agent": agent['name'],
            "type": "rebuttal",
            "content": rebuttal
        })
        
        print(f"{agent['emoji']} {agent['name']}: {rebuttal}\n")
    
    # ============================================================
    # ROUND 3: Each agent votes for best strategy
    # ============================================================
    print("\n🗳️  ROUND 3: VOTING")
    print("-" * 80)
    
    votes = {}
    for agent in AGENTS:
        persona = load_persona(agent['persona_file'])
        
        # Format full debate history
        history_text = format_debate_for_voting(debate_history, proposals)
        
        prompt = f"""Here is the complete debate:

{history_text}

Vote for the strategy that best serves this church's needs. You may vote for your own proposal or another agent's.

Respond with ONLY the agent name you're voting for. Choose from: {', '.join([a['name'] for a in AGENTS])}

Your vote:"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": persona},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temp for voting = more consistent
            max_tokens=20
        )
        
        vote = response.choices[0].message.content.strip()
        
        # Normalize vote (handle variations like "I vote for Planner" -> "Planner")
        for agent_config in AGENTS:
            if agent_config['name'].lower() in vote.lower():
                vote = agent_config['name']
                break
        
        votes[agent['name']] = vote
        
        debate_history.append({
            "round": 3,
            "agent": agent['name'],
            "type": "vote",
            "content": vote
        })
        
        print(f"{agent['emoji']} {agent['name']} votes for: {vote}")
    
    # ============================================================
    # Determine winner
    # ============================================================
    vote_counts = {}
    for voted_for in votes.values():
        vote_counts[voted_for] = vote_counts.get(voted_for, 0) + 1
    
    winner_name = max(vote_counts, key=vote_counts.get)
    winning_proposal = proposals[winner_name]
    
    print("\n" + "="*80)
    print("🏆 DEBATE OUTCOME")
    print("="*80)
    print(f"Winner: {winner_name} ({vote_counts[winner_name]}/{len(AGENTS)} votes)")
    print(f"Strategy: {winning_proposal}")
    print(f"Vote breakdown: {vote_counts}")
    print("="*80 + "\n")
    
    # ============================================================
    # Extract structured params from winning strategy
    # ============================================================
    print("🔧 Extracting structured parameters from winning strategy...")
    
    params = await extract_params_from_strategy(
        winning_proposal=winning_proposal,
        template=template,
        original_request=request,
        client=client
    )
    
    print(f"✅ Extracted params: {json.dumps(params, indent=2)}\n")
    
    # ============================================================
    # Update state with debate results
    # ============================================================
    state['debate_history'] = debate_history
    state['winning_agent'] = winner_name
    state['winning_strategy'] = winning_proposal
    state['vote_tally'] = vote_counts
    state['params'] = params
    
    return state


async def extract_params_from_strategy(
    winning_proposal: str,
    template,
    original_request: str,
    client: OpenAI
) -> Dict[str, Any]:
    """
    Convert winning strategy text into structured parameters.
    Uses the template schemas you already have.
    """
    from ..templates import get_params_model
    
    ParamsModel = get_params_model(template)
    
    extraction_prompt = f"""You are extracting structured parameters from a winning debate strategy.

ORIGINAL REQUEST:
{original_request}

WINNING STRATEGY:
{winning_proposal}

TASK:
Extract structured parameters that match the {template.value} template schema.
Use the strategy's reasoning and priorities, but ensure all required fields are filled with realistic values.

For data sources, use these available entities:
- People (volunteers, visitors, members)
- Groups (roles, small groups, serving teams)
- Gifts (donations)

Be specific and actionable. The parameters you extract will be executed immediately."""

    response = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "You are a parameter extraction specialist for church operations workflows."},
            {"role": "user", "content": extraction_prompt}
        ],
        response_format=ParamsModel,
        temperature=0.2
    )
    
    return response.choices[0].message.parsed.model_dump()


def format_debate_for_voting(history: List[Dict], proposals: Dict[str, str]) -> str:
    """Format debate history for voting context"""
    lines = []
    
    lines.append("ROUND 1 - PROPOSALS:")
    for agent_name, proposal in proposals.items():
        lines.append(f"  {agent_name}: {proposal}")
    
    lines.append("\nROUND 2 - REBUTTALS:")
    for entry in history:
        if entry['type'] == 'rebuttal':
            lines.append(f"  {entry['agent']}: {entry['content']}")
    
    return "\n".join(lines)