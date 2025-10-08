"""
Parameter Extraction - Convert winning strategy into structured params
Reuses existing extraction prompts but adds debate context
"""

import os
from pathlib import Path
from openai import OpenAI
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
PROMPTS_DIR = PROJECT_ROOT / "prompts"

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def load_extraction_prompt(template_type) -> str:
    """Load template-specific extraction prompt (reuses existing prompts)"""
    prompt_name = f"extract_params_{template_type}"
    prompt_path = PROMPTS_DIR / f"{prompt_name}.txt"
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt not found: {prompt_path}")
    
    return prompt_path.read_text()


def extract_params_from_winner(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract structured parameters from the winning debate strategy.
    
    Uses existing extraction prompts but enhances with debate context.
    
    Args:
        state: Orchestrator state with debate complete and winner determined
        
    Returns:
        Updated state with 'params' field populated
    """
    from ...templates import get_params_model
    
    debate_state = state['debate_state']
    
    winning_agent = debate_state['winning_agent']
    winning_strategy = debate_state['winning_strategy']
    template = debate_state['template']
    request = debate_state['request']
    
    print("\n" + "="*80)
    print("🔧 EXTRACTING PARAMETERS FROM WINNING STRATEGY")
    print("="*80)
    print(f"Winner: {winning_agent}")
    print(f"Strategy: {winning_strategy[:200]}...")
    print()
    
    # Get the appropriate Pydantic model for this template
    ParamsModel = get_params_model(template)
    
    # Load the existing extraction prompt for this template
    base_extraction_prompt = load_extraction_prompt(template.value)
    
    # Enhance with debate context
    enhanced_prompt = f"""You are extracting structured parameters from a WINNING DEBATE STRATEGY.

        CONTEXT:
        This request went through a multi-agent debate. Three agents (Planner, Operations, HumanFlourishing) proposed different strategies, and {winning_agent} won the debate with the following approach.

        ORIGINAL REQUEST:
        {request}

        WINNING AGENT: {winning_agent}

        WINNING STRATEGY:
        {winning_strategy}

        INSTRUCTIONS:
        {base_extraction_prompt}

        IMPORTANT: Use the winning agent's strategic priorities when making parameter choices:
        - Planner prioritizes: efficiency, capacity balancing, scalability
        - Operations prioritizes: feasibility, avoiding over-scheduling, practical execution  
        - HumanFlourishing prioritizes: relationships, spiritual growth, community health

        Extract parameters that align with {winning_agent}'s approach as described in their winning strategy.
    """

    # Call LLM with structured output
    response = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "You are a parameter extraction specialist for church operations workflows."},
            {"role": "user", "content": enhanced_prompt}
        ],
        response_format=ParamsModel,
        temperature=0.2
    )
    
    params = response.choices[0].message.parsed.model_dump()
    
    # Update both debate_state and top-level state
    debate_state['params'] = params
    state['params'] = params
    
    print(f"✅ Parameters extracted successfully")
    print(f"   Template: {template.value}")
    print(f"   Source: {params.get('source', {}).get('entity_type', 'N/A')}")
    if 'target' in params:
        print(f"   Target: {params['target'].get('entity_type', 'N/A')}")
    if 'match_strategy' in params:
        print(f"   Strategy: {params['match_strategy']}")
    print("="*80 + "\n")
    
    return state