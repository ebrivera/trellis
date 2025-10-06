"""
Extractor Node - Step 2 of orchestration pipeline
Extracts structured parameters based on template type
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from typing import Dict, Any
from ..schemas import (
    TemplateType, 
    MatchingParams, 
    MonitoringParams, 
    AnalysisParams,
    get_params_model
)

PROJECT_ROOT = Path(__file__).parent.parent.parent
PROMPTS_DIR = PROJECT_ROOT / "prompts"
load_dotenv()


def load_prompt(template_type: TemplateType) -> str:
    """Load template-specific prompt"""
    prompt_name = f"extract_params_{template_type.value}"
    prompt_path = PROMPTS_DIR / f"{prompt_name}.txt"
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt not found: {prompt_path}")
    
    return prompt_path.read_text()

def extract_params(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract structured parameters for a workflow template.
    
    Args:
        state: Dict containing:
            - 'request': str - natural language request
            - 'template': TemplateType - which template to use
            
    Returns:
        Updated state with:
            - 'params': dict - extracted parameters matching template schema
            - 'clarifications': list - any validation questions
    """
    request = state.get('request')
    template = state.get('template')
    
    if not request or not template:
        raise ValueError("State must contain 'request' and 'template'")
    
    # Get the appropriate Pydantic model for this template
    ParamsModel = get_params_model(template)
    
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Load template-specific prompt
    system_prompt = load_prompt(template)
    
    try:
        # Call LLM with structured output
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Request: {request}"}
            ],
            response_format=ParamsModel,
            temperature=0.2  # Slightly higher than classifier for creativity
        )
        
        params = completion.choices[0].message.parsed
        
        # Validate params (Pydantic already did basic validation)
        validation_errors = validate_params(params, state)
        
        if validation_errors:
            if 'clarifications' not in state:
                state['clarifications'] = []
            state['clarifications'].extend(validation_errors)
            print(f"⚠ Validation issues found:")
            for error in validation_errors:
                print(f"  - {error}")
        
        # Store params as dict for easy serialization
        state['params'] = params.model_dump()
        
        print(f"✓ Extracted {template.value} parameters")
        print(f"  Source: {_summarize_source(params)}")
        if hasattr(params, 'target'):
            print(f"  Target: {_summarize_target(params)}")
        if hasattr(params, 'metrics'):
            print(f"  Metrics: {len(params.metrics)} calculated")
        
        return state
        
    except Exception as e:
        error_msg = f"Parameter extraction failed: {str(e)}"
        state['errors'] = state.get('errors', []) + [error_msg]
        raise


def validate_params(params, state: Dict[str, Any]) -> list[str]:
    """
    Validate extracted parameters against business rules.
    
    Returns list of validation error messages (empty if valid)
    """
    errors = []
    
    # For demo purposes with Derek's test data, we skip file validation
    # In production, this would check available_files in state
    
    # Validate matching params
    if isinstance(params, MatchingParams):
        # Check that source and target are different
        if params.source.entity_type == params.target.entity_type:
            # This is OK for mentor-mentee matching (Person to Person)
            pass
        
        # Validate match fields reference actual columns
        # (In production, would query schema)
        valid_fields = ['interests', 'availability_days', 'zip', 'capacity']
        for field in params.match_fields.score_on:
            if field not in valid_fields:
                errors.append(f"Unknown match field: '{field}'. Available: {valid_fields}")
    
    # Validate monitoring params
    elif isinstance(params, MonitoringParams):
        # Check time field exists
        valid_time_fields = ['visit_date', 'gift_date', 'last_contact_date', 'created_at']
        if params.condition.time_field not in valid_time_fields:
            errors.append(f"Unknown time field: '{params.condition.time_field}'. Available: {valid_time_fields}")
    
    # Validate analysis params
    elif isinstance(params, AnalysisParams):
        # Check that join_on makes sense for the sources
        if params.join_on:
            valid_joins = ['initiative_id', 'donor_id', 'leader_id']
            if params.join_on not in valid_joins:
                errors.append(f"Unknown join field: '{params.join_on}'. Available: {valid_joins}")
    
    return errors


def _summarize_source(params) -> str:
    """Helper to print source info"""
    if isinstance(params, MatchingParams):
        filters = f" with {len(params.source.filters)} filters" if params.source.filters else ""
        return f"{params.source.entity_type.value}{filters}"
    elif isinstance(params, MonitoringParams):
        return f"{params.source.entity_type.value}"
    elif isinstance(params, AnalysisParams):
        return f"{len(params.sources)} sources"
    return "unknown"


def _summarize_target(params) -> str:
    """Helper to print target info"""
    if isinstance(params, MatchingParams):
        return f"{params.target.entity_type.value}"
    return ""


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Must run classifier first to set template
    from .classifier import classify_template
    
    test_cases = {
        "volunteers": {
            "request": "Track volunteer availability and auto-assign to Sunday roles",
            "expected_template": TemplateType.MATCHING,
        },
        "visitors": {
            "request": "Monitor first-time visitors and flag ones we haven't contacted in 2 weeks",
            "expected_template": TemplateType.MONITORING,
        },
        "giving": {
            "request": "Show giving trends by initiative with lapsed-donor alerts",
            "expected_template": TemplateType.ANALYSIS,
        },
        "mentoring": {
            "request": "Match mentors to mentees based on interests and send intro messages",
            "expected_template": TemplateType.MATCHING,
        },
    }
    
    print("=" * 80)
    print("EXTRACTOR NODE TESTS")
    print("=" * 80)
    
    for name, test_case in test_cases.items():
        print(f"\n{'─' * 80}")
        print(f"TEST: {name}")
        print(f"Request: '{test_case['request']}'")
        print('─' * 80)
        
        # First classify to get template
        state = {"request": test_case['request']}
        state = classify_template(state)
        
        # Verify classification
        assert state['template'] == test_case['expected_template'], \
            f"Expected {test_case['expected_template']}, got {state['template']}"
        
        print(f"\nExtracting parameters for {state['template'].value} template...")
        print()
        
        try:
            # Extract params
            state = extract_params(state)
            
            # Validate against schema
            ParamsModel = get_params_model(state['template'])
            validated_params = ParamsModel(**state['params'])
            
            print(f"\n✓ Parameters validated successfully!")
            print(f"\nExtracted params preview:")
            
            # Pretty print key params
            if isinstance(validated_params, MatchingParams):
                print(f"  - Source: {validated_params.source.entity_type.value}")
                print(f"  - Target: {validated_params.target.entity_type.value}")
                print(f"  - Strategy: {validated_params.match_strategy.value}")
                print(f"  - Notifications: {len(validated_params.notifications)}")
                
            elif isinstance(validated_params, MonitoringParams):
                print(f"  - Source: {validated_params.source.entity_type.value}")
                print(f"  - Time field: {validated_params.condition.time_field}")
                print(f"  - Threshold: {validated_params.condition.threshold}")
                print(f"  - Alerts: {len(validated_params.alerts)}")
                
            elif isinstance(validated_params, AnalysisParams):
                print(f"  - Sources: {len(validated_params.sources)}")
                print(f"  - Metrics: {len(validated_params.metrics)}")
                print(f"  - Flags: {len(validated_params.flags) if validated_params.flags else 0}")
            
            print(f"\n✓ Test passed!")
            
        except Exception as e:
            print(f"✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("TESTS COMPLETE")
    print("=" * 80)