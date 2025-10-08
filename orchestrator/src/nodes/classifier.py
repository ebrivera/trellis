"""
./orchestrator/src/nodes/classifier.py
Classifier Node - Step 1 of orchestration pipeline
Determines which workflow template to use based on natural language request
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from typing import Dict, Any
from ..schemas import TemplateChoice, TemplateType

PROJECT_ROOT = Path(__file__).parent.parent.parent
PROMPTS_DIR = PROJECT_ROOT / "prompts"
load_dotenv()

def load_prompt(prompt_name: str) -> str:
    """Load prompt from prompts/ directory"""
    prompt_path = PROMPTS_DIR / f"{prompt_name}.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt not found: {prompt_path}")
    return prompt_path.read_text()


def classify_template(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify a natural language request into one of 3 workflow templates.
    
    Args:
        state: Dict containing 'request' (str) - the user's natural language input
        
    Returns:
        Updated state with:
        - 'template': TemplateType enum value
        - 'confidence': float 0-1
        - 'clarifications': List[str] with question if confidence < 0.8
    """
    request = state.get('request')
    if not request:
        raise ValueError("State must contain 'request' field")
    
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Load system prompt
    system_prompt = load_prompt('classify_template')
    
    # Call LLM with structured output
    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",  # Supports structured outputs
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Request: {request}"}
            ],
            response_format=TemplateChoice,
            temperature=0.1  # Low temperature for consistent classification
        )
        
        result = completion.choices[0].message.parsed
        
        # Update state
        state['template'] = result.template
        state['confidence'] = result.confidence
        
        # Add clarifying question if confidence is low
        if result.confidence < 0.8 and result.clarifying_question:
            if 'clarifications' not in state:
                state['clarifications'] = []
            state['clarifications'].append(result.clarifying_question)
        
        # Store reasoning for debugging
        state['classifier_reasoning'] = result.reasoning
        
        print(f"✓ Classified as: {result.template.value}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Reasoning: {result.reasoning}")
        
        if result.clarifying_question:
            print(f"  ⚠ Clarifying question: {result.clarifying_question}")
        
        return state
        
    except Exception as e:
        state['errors'] = state.get('errors', []) + [f"Classification failed: {str(e)}"]
        raise


# ============================================================================
# TESTING - Run this file directly to test classification
# ============================================================================

if __name__ == "__main__":
    # Test cases from your technical doc
    test_requests = {
        "volunteers": "Track volunteer availability and auto-assign to Sunday roles",
        "visitors": "Monitor first-time visitors and flag ones we haven't contacted in 2 weeks",
        "giving": "Show giving trends by initiative with lapsed-donor alerts",
        "mentoring": "Match mentors to mentees based on interests and send intro messages",
        "ambiguous": "Help with volunteers",  # Should trigger clarifying question
    }
    
    print("=" * 80)
    print("CLASSIFIER NODE TESTS")
    print("=" * 80)
    
    for name, request in test_requests.items():
        print(f"\n{'─' * 80}")
        print(f"TEST: {name}")
        print(f"Request: '{request}'")
        print('─' * 80)
        
        state = {"request": request}
        
        try:
            result_state = classify_template(state)
            
            # Validate expected results
            if name == "volunteers":
                assert result_state['template'] == TemplateType.MATCHING
                assert result_state['confidence'] > 0.85
                
            elif name == "visitors":
                assert result_state['template'] == TemplateType.MONITORING
                assert result_state['confidence'] > 0.85
                
            elif name == "giving":
                assert result_state['template'] == TemplateType.ANALYSIS
                assert result_state['confidence'] > 0.80
                
            elif name == "mentoring":
                assert result_state['template'] == TemplateType.MATCHING
                assert result_state['confidence'] > 0.85
                
            elif name == "ambiguous":
                # Should have low confidence and clarifying question
                assert result_state['confidence'] < 0.8
                assert len(result_state.get('clarifications', [])) > 0
            
            print("✓ Test passed!")
            
        except AssertionError as e:
            print(f"✗ Test failed: {e}")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    print("\n" + "=" * 80)
    print("TESTS COMPLETE")
    print("=" * 80)