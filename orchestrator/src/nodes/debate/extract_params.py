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
    NOTE: Extraction prompts use EntityQuery schema (entity_type + subtype, not CSV files).
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
    
    # Get the appropriate Pydantic model (uses EntityQuery schema)
    ParamsModel = get_params_model(template)
    
    # Load the extraction prompt for this template
    base_extraction_prompt = load_extraction_prompt(template.value)
    
    # Enhance with debate context
    enhanced_prompt = f"""You are extracting structured parameters from a WINNING DEBATE STRATEGY.

    CONTEXT:
    This request went through a multi-agent debate. Three agents (Planner, Operations, HumanFlourishing) proposed different strategies, and {winning_agent} won the debate.

    ORIGINAL REQUEST:
    {request}

    WINNING AGENT: {winning_agent}

    WINNING STRATEGY:
    {winning_strategy}

    EXTRACTION INSTRUCTIONS:
    {base_extraction_prompt}

    AGENT PRIORITIES (use these to inform parameter choices):
    - Planner: efficiency, capacity balancing, scalability
    - Operations: feasibility, avoiding over-scheduling, practical execution  
    - HumanFlourishing: relationships, spiritual growth, community health

    Extract parameters that align with {winning_agent}'s approach as described in their winning strategy.
    """

    # Call LLM with structured output
    response = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "You are a parameter extraction specialist. Extract database queries, not file operations."},
            {"role": "user", "content": enhanced_prompt}
        ],
        response_format=ParamsModel,
        temperature=0.2
    )
    
    params = response.choices[0].message.parsed.model_dump()

    # Update state
    debate_state['params'] = params
    state['params'] = params

    print(f"✅ Parameters extracted successfully")
    print(f"   Template: {template.value}")

    # Log EntityQuery details
    if 'source' in params:
        source = params['source']
        print(f"   Source: {source.get('entity_type')}")
        if source.get('subtype'):
            print(f"     Subtype: {source['subtype']}")
        if source.get('filters'):
            print(f"     Filters: {len(source['filters'])} conditions")
            for filt in source['filters']:
                print(f"       - {filt}")

    if 'target' in params:
        target = params['target']
        print(f"   Target: {target.get('entity_type')}")
        if target.get('subtype'):
            print(f"     Subtype: {target['subtype']}")
        if target.get('filters'):
            print(f"     Filters: {len(target['filters'])} conditions")
            for filt in target['filters']:
                print(f"       - {filt}")

    # Print full params for debugging
    import json
    print(f"\n📋 FULL EXTRACTED PARAMS:")
    print(json.dumps(params, indent=2, default=str))

    print("="*80 + "\n")

    return state