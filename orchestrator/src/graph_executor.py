"""
Workflow Executor - Handles execution after approval
Separated from debate graph for clean separation of concerns
"""

import json
from typing import Dict, Any

from .database import insert_one, fetch_one, execute as db_execute, insert_many
from .schemas import TemplateType, EntityType
from .templates import MatchingParams, MonitoringParams, AnalysisParams, get_params_model
from .functions.load_data import load_data
from .functions.filter import filter_data, filter_by_time_condition
from .functions.match import match as match_func
from .functions.send_notification import send_notification
from .functions.calculate_metrics import calculate_metrics

from uuid import UUID
from datetime import datetime, date
import pandas as pd

def _serialize_preview(preview: Dict[str, Any]) -> Dict[str, Any]:
    """Convert non-JSON-serializable objects (UUID, Timestamp) to strings"""
    
    def convert_value(v):
        if isinstance(v, UUID):
            return str(v)
        elif isinstance(v, (datetime, date, pd.Timestamp)):
            return v.isoformat() if hasattr(v, 'isoformat') else str(v)
        elif isinstance(v, list):
            return [convert_value(item) for item in v]
        elif isinstance(v, dict):
            return {k: convert_value(val) for k, val in v.items()}
        elif pd.isna(v):  # Handle pandas NaN/NaT
            return None
        return v
    
    return {k: convert_value(v) for k, v in preview.items()}

# ============================================================================
# FIELD MAPPING: SAFETY NET FOR AI
# ============================================================================

def normalize_match_fields(match_fields):
    """
    Map common field name synonyms to actual database columns.
    Safety net in case AI uses wrong field names.
    
    Examples:
        'skills' → 'interests'
        'abilities' → 'interests'
        'availability' → 'availability_days'
    """
    field_mapping = {
        'skills': 'interests',
        'abilities': 'interests',
        'talents': 'interests',
        'experience': 'interests',
        'skill': 'interests',
        'ability': 'interests',
        'talent': 'interests',
        'availability': 'availability_days',
        'available': 'availability_days',
        'when_available': 'availability_days',
        'schedule': 'availability_days',
    }
    
    # If it's already a MatchFields object, convert to dict
    if hasattr(match_fields, 'model_dump'):
        match_fields_dict = match_fields.model_dump()
    else:
        match_fields_dict = match_fields
    
    # Normalize score_on fields
    if 'score_on' in match_fields_dict:
        match_fields_dict['score_on'] = [
            field_mapping.get(field.lower(), field) 
            for field in match_fields_dict['score_on']
        ]
    
    # Normalize weights
    if 'weights' in match_fields_dict:
        for weight_obj in match_fields_dict['weights']:
            if 'field' in weight_obj:
                original = weight_obj['field']
                weight_obj['field'] = field_mapping.get(original.lower(), original)
    
    return match_fields_dict


# ============================================================================
# PREVIEW GENERATION (Dry-run before approval)
# ============================================================================

async def generate_preview(template: TemplateType, params: Dict[str, Any], workflow_id: str) -> Dict[str, Any]:
    try:
        if template == TemplateType.MATCHING:
            return await _preview_matching(params)
        elif template == TemplateType.MONITORING:
            return await _preview_monitoring(params)
        elif template == TemplateType.ANALYSIS:
            return await _preview_analysis(params)
        else:
            return {"error": f"Unknown template: {template}"}
    except Exception as e:
        print(f"⚠️ Preview generation failed: {e}")
        return {
            "error": "Preview generation failed",
            "message": str(e),
            "proposed_assignments": 0,
            "source_count": 0,
            "target_count": 0
        }

async def _preview_matching(params: Dict[str, Any]) -> Dict[str, Any]:
    """Preview matching workflow"""
    from .templates.matching import MatchingParams, MatchFields

    # Parse params into Pydantic model
    params_model = MatchingParams(**params)

    # ADD THIS: Normalize field names before matching
    normalized_fields = normalize_match_fields(params_model.match_fields)
    params_model.match_fields = MatchFields(**normalized_fields)

    # Load data
    source_df = await load_data(
        EntityType(params_model.source.entity_type),
        params_model.source.subtype
    )
    target_df = await load_data(
        EntityType(params_model.target.entity_type),
        params_model.target.subtype
    )

    print(f"\n🔍 DEBUG: Loaded {len(source_df)} source entities ({params_model.source.subtype})")
    print(f"🔍 DEBUG: Loaded {len(target_df)} target entities ({params_model.target.subtype})")

    # Filter
    if params_model.source.filters:
        print(f"🔍 DEBUG: Applying {len(params_model.source.filters)} source filters...")
        for f in params_model.source.filters:
            print(f"   - {f.field} {f.operator} {f.value}")
        source_df = filter_data(source_df, params_model.source.filters)
        print(f"🔍 DEBUG: After filtering: {len(source_df)} source entities remain")
    if params_model.target.filters:
        print(f"🔍 DEBUG: Applying {len(params_model.target.filters)} target filters...")
        target_df = filter_data(target_df, params_model.target.filters)
        print(f"🔍 DEBUG: After filtering: {len(target_df)} target entities remain")

    # Match (dry-run)
    print(f"🔍 DEBUG: Running matching algorithm...")
    assignments = match_func(
        source_df,
        target_df,
        params_model.match_strategy,
        params_model.match_fields,
        params_model.constraints
    )
    print(f"🔍 DEBUG: Matching produced {len(assignments)} assignments")
    
    # Calculate preview metrics
    match_rate = len(assignments) / len(source_df) if len(source_df) > 0 else 0
    avg_score = sum(a['match_score'] for a in assignments) / len(assignments) if assignments else 0
    
    return _serialize_preview({
        "proposed_assignments": len(assignments),
        "match_rate": round(match_rate, 2),
        "avg_match_score": round(avg_score, 2),
        "assignments_preview": assignments[:10],  # First 10 for UI
        "source_count": len(source_df),
        "target_count": len(target_df),
        "notifications_planned": len(assignments) * len(params_model.notifications)
    })

async def _preview_monitoring(params: Dict[str, Any]) -> Dict[str, Any]:
    """Preview monitoring workflow"""
    from .templates.monitoring import MonitoringParams
    
    params_model = MonitoringParams(**params)
    
    # Load and filter by time condition
    df = await load_data(
    EntityType(params_model.source.entity_type),
    params_model.source.subtype
    )

    flagged = filter_by_time_condition(
        df,
        params_model.condition.time_field,
        params_model.condition.threshold,
        params_model.condition.operator
    )
    
    return _serialize_preview({
        "flagged_count": len(flagged),
        "total_scanned": len(df),
        "flagged_preview": flagged.head(10).to_dict('records'),
        "notifications_planned": len(flagged) * len(params_model.alerts)
    })


async def _preview_analysis(params: Dict[str, Any]) -> Dict[str, Any]:
    """Preview analysis workflow - shows what metrics will be calculated"""
    from .templates.analysis import AnalysisParams
    import pandas as pd

    params_model = AnalysisParams(**params)

    # Load data from first source
    first_source = params_model.sources[0]
    df = await load_data(
        EntityType(first_source.entity_type),
        first_source.subtype
    )

    print(f"🔍 DEBUG: Loaded {len(df)} {first_source.entity_type} records for analysis")

    # Handle joins if multiple sources specified
    if len(params_model.sources) > 1 and params_model.join_on:
        second_source = params_model.sources[1]
        join_df = await load_data(
            EntityType(second_source.entity_type),
            second_source.subtype
        )
        print(f"🔍 DEBUG: Loaded {len(join_df)} {second_source.entity_type} for join")

        # Perform join (left join to keep all records from first source)
        # Map initiative_id → name from groups table
        if 'id' in join_df.columns and 'name' in join_df.columns:
            # Create a mapping dict: UUID → name
            id_to_name = dict(zip(join_df['id'].astype(str), join_df['name']))
            # Add a new column with the initiative name
            if params_model.join_on in df.columns:
                df['initiative_name'] = df[params_model.join_on].astype(str).map(id_to_name)
                print(f"🔍 DEBUG: Mapped {df['initiative_name'].notna().sum()} initiative names")

                # Update metrics to use initiative_name instead of initiative_id
                for metric in params_model.metrics:
                    if metric.group_by == params_model.join_on:
                        metric.group_by = 'initiative_name'

    # Apply filters if present
    if first_source.filters:
        print(f"🔍 DEBUG: Applying {len(first_source.filters)} filters...")
        df = filter_data(df, first_source.filters)
        print(f"🔍 DEBUG: After filtering: {len(df)} records remain")

    # Calculate metrics
    metrics_result = calculate_metrics(params_model.metrics, df)
    print(f"🔍 DEBUG: Calculated metrics: {metrics_result}")

    # Determine if any metrics are grouped (produce multiple values)
    grouped_metrics = {
        name: value for name, value in metrics_result.items()
        if isinstance(value, dict) and 'error' not in value
    }

    scalar_metrics = {
        name: value for name, value in metrics_result.items()
        if not isinstance(value, dict) or 'error' in value
    }

    return _serialize_preview({
        "total_analyzed": len(df),
        "metrics": metrics_result,
        "grouped_metrics": list(grouped_metrics.keys()),
        "scalar_metrics": list(scalar_metrics.keys()),
        "report_summary": f"Analysis of {len(df)} {first_source.entity_type} records with {len(params_model.metrics)} metrics",
        "source_type": first_source.entity_type  # Use entity_type instead of subtype
    })


# ============================================================================
# WORKFLOW EXECUTION (After approval)
# ============================================================================

async def execute_workflow(approval_id: str, approved_by: str = "system") -> Dict[str, Any]:
    """
    Execute approved workflow: create assignments, send notifications.
    Called by POST /approval/{id}/decide when action=approve.
    """
    # Fetch approval gate
    approval = await fetch_one(
        "SELECT * FROM approval_gates WHERE id = $1",
        approval_id
    )
    
    if not approval:
        raise ValueError(f"Approval gate not found: {approval_id}")
    
    # Fetch workflow run
    workflow = await fetch_one(
        "SELECT * FROM workflow_runs WHERE id = $1",
        approval['workflow_run_id']
    )
    
    if not workflow:
        raise ValueError(f"Workflow run not found: {approval['workflow_run_id']}")
    
    # Parse params
    params = workflow['extracted_params']
    if isinstance(params, str):
        params = json.loads(params)
    
    template = TemplateType(workflow['template_type'])
    
    # Execute based on template
    try:
        if template == TemplateType.MATCHING:
            result = await execute_matching(params, workflow['id'])
        elif template == TemplateType.MONITORING:
            result = await execute_monitoring(params, workflow['id'])
        elif template == TemplateType.ANALYSIS:
            result = await execute_analysis(params, workflow['id'])
        else:
            raise ValueError(f"Unknown template: {template}")
        
        # Update workflow run
        await db_execute(
            "UPDATE workflow_runs SET status = $1, completed_at = NOW(), results = $2::jsonb WHERE id = $3",
            "completed",
            json.dumps(result),
            workflow['id']
        )
        
        return result
        
    except Exception as e:
        # Mark as failed
        await db_execute(
            "UPDATE workflow_runs SET status = $1, error = $2 WHERE id = $3",
            "failed",
            str(e),
            workflow['id']
        )
        raise


async def execute_matching(params: Dict[str, Any], workflow_run_id: str) -> Dict[str, Any]:
    """Execute matching workflow: load → filter → match → assignments → notify"""
    from .templates.matching import MatchingParams, MatchFields
    
    params_model = MatchingParams(**params)
    
    normalized_fields = normalize_match_fields(params_model.match_fields)
    params_model.match_fields = MatchFields(**normalized_fields)
    
    # Step 1: Load data
    source_df = await load_data(
        EntityType(params_model.source.entity_type),
        params_model.source.subtype
    )
    target_df = await load_data(
        EntityType(params_model.target.entity_type),
        params_model.target.subtype
    )
    
    # Step 2: Filter
    if params_model.source.filters:
        source_df = filter_data(source_df, params_model.source.filters)
    if params_model.target.filters:
        target_df = filter_data(target_df, params_model.target.filters)
    
    # Step 3: Match
    assignments = match_func(
        source_df,
        target_df,
        params_model.match_strategy,
        params_model.match_fields,
        params_model.constraints
    )
    
    # Step 4: Create assignments in database
    assignment_records = [
        {
            "source_id": a['source_id'],
            "target_id": a['target_id'],
            "target_type": "group" if params_model.target.entity_type == EntityType.GROUP else "person",
            "assignment_type": f"{params_model.source.subtype}_to_{params_model.target.subtype}",
            "match_score": a['match_score'],
            "status": "active",
            "workflow_run_id": workflow_run_id
        }
        for a in assignments
    ]
    
    if assignment_records:
        await insert_many("assignments", assignment_records)
    
    # Step 5: Send notifications
    notification_results = []
    for notif_config in params_model.notifications:
        # Determine recipients
        if notif_config.recipient_type == "source":
            recipient_ids = [str(a['source_id']) for a in assignments]
            recipients = source_df[source_df['id'].astype(str).isin(recipient_ids)].to_dict('records')
        elif notif_config.recipient_type in ["target", "target_owners"]:
            recipient_ids = [str(a['target_id']) for a in assignments]
            recipients = target_df[target_df['id'].astype(str).isin(recipient_ids)].to_dict('records')
        else:
            recipients = []
        
        if recipients:
            result = await send_notification(
                recipients,
                notif_config,
                {},
                db_insert=True,
                workflow_run_id=workflow_run_id
            )
            notification_results.append(result)

    # Calculate final metrics
    match_rate = len(assignments) / len(source_df) if len(source_df) > 0 else 0
    
    return {
        "assignments_created": len(assignments),
        "notifications_sent": sum(r.get('sent', 0) for r in notification_results),
        "match_rate": round(match_rate, 2),
        "avg_match_score": round(sum(a['match_score'] for a in assignments) / len(assignments), 2) if assignments else 0
    }


async def execute_monitoring(params: Dict[str, Any], workflow_run_id: str) -> Dict[str, Any]:
    """Execute monitoring workflow: load → filter by time → notify"""
    from .templates.monitoring import MonitoringParams
    
    params_model = MonitoringParams(**params)
    
    # Load and filter
    df = await load_data(
        EntityType(params_model.source.entity_type),
        params_model.source.subtype
    )

    flagged = filter_by_time_condition(
        df,
        params_model.condition.time_field,
        params_model.condition.threshold,
        params_model.condition.operator
    )
    
    # Send notifications
    notification_results = []
    for notif_config in params_model.alerts:
        recipients = flagged.to_dict('records')
        if recipients:
            result = await send_notification(
                recipients,
                notif_config,
                {},
                db_insert=True,
                workflow_run_id=workflow_run_id
            )
            notification_results.append(result)
    
    return {
        "flagged_count": len(flagged),
        "notifications_sent": sum(r.get('sent', 0) for r in notification_results)
    }


async def execute_analysis(params: Dict[str, Any], workflow_run_id: str) -> Dict[str, Any]:
    """Execute analysis workflow: load → filter → calculate metrics → store results"""
    from .templates.analysis import AnalysisParams
    import pandas as pd

    params_model = AnalysisParams(**params)

    # Load data from first source
    first_source = params_model.sources[0]
    df = await load_data(
        EntityType(first_source.entity_type),
        first_source.subtype
    )

    print(f"📊 Analysis: Loaded {len(df)} {first_source.entity_type} records")

    # Handle joins if multiple sources specified
    if len(params_model.sources) > 1 and params_model.join_on:
        second_source = params_model.sources[1]
        join_df = await load_data(
            EntityType(second_source.entity_type),
            second_source.subtype
        )
        print(f"📊 Analysis: Loaded {len(join_df)} {second_source.entity_type} for join")

        # Perform join - map initiative_id → name from groups table
        if 'id' in join_df.columns and 'name' in join_df.columns:
            # Create a mapping dict: UUID → name
            id_to_name = dict(zip(join_df['id'].astype(str), join_df['name']))
            # Add a new column with the initiative name
            if params_model.join_on in df.columns:
                df['initiative_name'] = df[params_model.join_on].astype(str).map(id_to_name)
                print(f"📊 Analysis: Mapped {df['initiative_name'].notna().sum()} initiative names")

                # Update metrics to use initiative_name instead of initiative_id
                for metric in params_model.metrics:
                    if metric.group_by == params_model.join_on:
                        metric.group_by = 'initiative_name'

    # Apply filters if present
    if first_source.filters:
        print(f"📊 Analysis: Applying {len(first_source.filters)} filters...")
        df = filter_data(df, first_source.filters)
        print(f"📊 Analysis: After filtering: {len(df)} records remain")

    # Calculate metrics
    metrics_result = calculate_metrics(params_model.metrics, df)
    print(f"📊 Analysis: Calculated {len(metrics_result)} metrics")

    # Format results for display
    result_summary = {
        "entities_analyzed": len(df),
        "metrics": metrics_result,
        "source_type": first_source.entity_type,  # Use entity_type instead of subtype
        "metric_count": len(metrics_result)
    }

    # Note: Analysis workflows produce REPORTS, not individual notifications
    # If notifications are needed, they should go to admins as summary reports
    # Individual person notifications should use Monitoring template instead

    print(f"✅ Analysis complete: {len(df)} records analyzed, {len(metrics_result)} metrics calculated")

    return result_summary