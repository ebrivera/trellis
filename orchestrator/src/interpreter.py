import json
import os
from typing import Dict, Any, Optional
from openai import OpenAI
from models import GoalSpec
from dotenv import load_dotenv


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


INTERPRETER_PROMPT = """
You are a church operations planning assistant. Your job is to convert natural language requests into structured JSON goals.

You MUST output valid JSON with these exact fields:
- objective: (string) Single clear sentence describing the goal
- constraints: (array of strings) Hard rules like "no texts after 9pm", "only adults", etc.
- kpis: (array of strings) Metrics to track. Examples: "placement_coverage_pct", "message_delivery_rate", "group_balance_score"
- inputs_required: (array of strings) Data sources needed. Examples: "people_sheet", "groups_sheet", "giving_data"
- assumptions: (array of strings) Things you're inferring from the request
- risk_flags: (array of strings) Things that need approval. Examples: "large_blast_requires_approval" (>200 recipients), "PII_export", "financial_data_access"

**Policy awareness:**
- If messaging >50 people, add "large_blast_requires_approval" to risk_flags
- If exporting data, add "data_export_requires_review" to risk_flags
- If the request is vague about data sources, add them to inputs_required and note in assumptions

Output ONLY valid JSON. No markdown, no explanations."""

def interpret_goal(ask: str, context: Optional[Dict[str, Any]] = None) -> GoalSpec:
    """
    Convert natural language ask into a structured GoalSpec.
    
    Args:
        ask: User's natural language request
        context: Optional context (org info, previous plans, etc.)
    
    Returns:
        GoalSpec object
    
    Raises:
        ValueError: If LLM output is invalid and can't be repaired
    """
    
    # Build the prompt
    user_message = f"Request: {ask}"
    if context:
        user_message += f"\n\nContext: {json.dumps(context, indent=2)}"
    
    try:
        # Call OpenAI
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": INTERPRETER_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.1,  # Low temperature for consistency
            response_format={"type": "json_object"}  # Force JSON output
        )
        
        # Parse response
        raw_json = response.choices[0].message.content
        parsed = json.loads(raw_json)
        
        # Validate with Pydantic
        try:
            goalspec = GoalSpec(**parsed)
            return goalspec
        except Exception as validation_error:
            # Auto-repair attempt
            repaired = _attempt_repair(parsed, str(validation_error))
            return GoalSpec(**repaired)
            
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON: {e}")
    except Exception as e:
        raise ValueError(f"Failed to interpret goal: {e}")


def _attempt_repair(parsed: Dict[str, Any], error_msg: str) -> Dict[str, Any]:
    """
    Simple auto-repair for common issues.
    
    Common fixes:
    - Missing kpis → add default
    - Empty inputs_required when obvious (mentions "sheet", "data")
    """
    repaired = parsed.copy()
    
    # Add default KPIs if missing
    if not repaired.get("kpis"):
        repaired["kpis"] = ["placement_coverage_pct"]
    
    # Ensure all fields exist
    for field in ["objective", "constraints", "kpis", "inputs_required", "assumptions", "risk_flags"]:
        if field not in repaired:
            repaired[field] = [] if field != "objective" else "No clear objective provided"
    
    return repaired