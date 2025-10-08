# orchestrator/src/graph.py
"""
Orchestration graph: NL request → template classification → param extraction → execution
"""

import json
from typing import Dict, Any, Optional
from uuid import uuid4
from datetime import datetime
import pandas as pd

from .nodes.classifier import classify_template
from .nodes.extractor import extract_params
from .database import insert_one, fetch_one, execute as db_execute, insert_many
from .schemas import TemplateType, EntityType
from .templates import MatchingParams, MonitoringParams, AnalysisParams, get_params_model
from .functions.load_data import load_data
from .functions.filter import filter_data, filter_by_time_condition
from .functions.match import match as match_func
from .functions.send_notification import send_notification
from .functions.calculate_metrics import calculate_metrics


# ============================================================================
# MAIN ORCHESTRATION PIPELINE
# ============================================================================

async def orchestrate_request(request: str, available_files: list[str] = None) -> Dict[str, Any]:
    """
    Main orchestration pipeline: NL request → classify → extract → create approval gate.
    
    Args:
        request: Natural language request from user
        available_files: Optional list of available CSV files
        
    Returns:
        Dict with approval_id, workflow_id, template, params, clarifications
    """
    if available_files is None:
        available_files = []
    
    # Create workflow run record
    workflow_id = str(uuid4())
    await insert_one("workflow_runs", {
        "id": workflow_id,
        "template_type": "classifying",  # Will update after classification
        "status": "classifying",
        "request_text": request,
    })
    
    # Step 1: Classify template
    state = {
        "request": request,
        "available_files": available_files
    }
    state = classify_template(state)
    
    # Update workflow with template
    await db_execute(
        "UPDATE workflow_runs SET template_type = $1, status = $2 WHERE id = $3",
        state['template'].value, "extracting_params", workflow_id
    )
    
    # Step 2: Extract parameters
    state = extract_params(state)
    
    # Update workflow with extracted params
    await db_execute(
        "UPDATE workflow_runs SET extracted_params = $1::jsonb, status = $2 WHERE id = $3",
        json.dumps(state['params']),  # Convert dict to JSON string
        "awaiting_approval", 
        workflow_id
    )
    
    # Step 3: Generate preview (execute dry-run without commits)
    preview_data = await _generate_preview(state['template'], state['params'], workflow_id)
    
    # Step 4: Create approval gate
    approval_id = str(uuid4())
    await insert_one("approval_gates", {
        "id": approval_id,
        "workflow_run_id": workflow_id,
        "gate_type": state['template'].value,
        "preview_data": preview_data,
        "status": "pending",
    })
    
    return {
        "approval_id": approval_id,
        "workflow_id": workflow_id,
        "template": state['template'].value,
        "params": state['params'],
        "clarifications": state.get('clarifications', []),
        "preview": preview_data
    }


async def execute_workflow(approval_id: str) -> Dict[str, Any]:
    """
    Execute approved workflow: load gate → execute template → update records.
    
    Args:
        approval_id: UUID of the approval gate
        
    Returns:
        Dict with execution results
    """
    # Load approval gate
    gate = await fetch_one("SELECT * FROM approval_gates WHERE id = $1", approval_id)
    if not gate:
        raise ValueError(f"Approval gate {approval_id} not found")
    
    if gate['status'] != 'approved':
        raise ValueError(f"Cannot execute workflow: gate status is {gate['status']}")
    
    # Load workflow run
    workflow = await fetch_one("SELECT * FROM workflow_runs WHERE id = $1", gate['workflow_run_id'])
    if not workflow:
        raise ValueError(f"Workflow run {gate['workflow_run_id']} not found")
    
    # Update workflow status
    await db_execute(
        "UPDATE workflow_runs SET status = $1 WHERE id = $2",
        "executing", workflow['id']
    )
    
    # Parse template and params
    template = TemplateType(workflow['template_type'])
    params_dict = workflow['extracted_params']
    if isinstance(params_dict, str):
        params_dict = json.loads(params_dict)  # Parse JSON string back to dict
    
    # Validate params against schema
    ParamsModel = get_params_model(template)
    params = ParamsModel(**params_dict)
    
    # Execute based on template
    try:
        if template == TemplateType.MATCHING:
            result = await execute_matching(params, workflow['id'])
        elif template == TemplateType.MONITORING:
            result = await execute_monitoring(params, workflow['id'])
        elif template == TemplateType.ANALYSIS:
            result = await execute_analysis(params, workflow['id'])
        else:
            raise ValueError(f"Unknown template type: {template}")
        
        # Update workflow as completed
        await db_execute(
            "UPDATE workflow_runs SET status = $1, completed_at = NOW(), results = $2::jsonb WHERE id = $3",
            "completed", json.dumps(result), workflow['id']  # Convert result to JSON string
        )
        
        return result
        
    except Exception as e:
        # Update workflow as failed
        await db_execute(
            "UPDATE workflow_runs SET status = $1, error = $2 WHERE id = $3",
            "failed", str(e), workflow['id']
        )
        raise


# ============================================================================
# PREVIEW GENERATION (Dry-run execution)
# ============================================================================

async def _generate_preview(template: TemplateType, params_dict: Dict[str, Any], workflow_id: str) -> Dict[str, Any]:
    """Generate preview data for approval UI without committing changes."""
    
    ParamsModel = get_params_model(template)
    params = ParamsModel(**params_dict)
    
    if template == TemplateType.MATCHING:
        return await _preview_matching(params)
    elif template == TemplateType.MONITORING:
        return await _preview_monitoring(params)
    elif template == TemplateType.ANALYSIS:
        return await _preview_analysis(params)
    
    return {}


async def _preview_matching(params: MatchingParams) -> Dict[str, Any]:
    """Generate matching preview without creating assignments."""
    
    # Load source and target data
    source_df = await load_data(params.source.entity_type, params.source.subtype)
    target_df = await load_data(params.target.entity_type, params.target.subtype)
    
    # Apply filters if specified
    if params.source.filters:
        source_df = filter_data(source_df, params.source.filters)
    if params.target.filters:
        target_df = filter_data(target_df, params.target.filters)
    
    # Run matching algorithm
    assignments = match_func(
        source_df,
        target_df,
        params.match_strategy,
        params.match_fields,
        params.constraints
    )
    
    # Calculate metrics
    total_source = len(source_df)
    matched = len(assignments)
    unmatched = total_source - matched
    match_rate = matched / total_source if total_source > 0 else 0
    avg_score = sum(a['match_score'] for a in assignments) / matched if matched > 0 else 0
    
    # Find unmatched entities
    matched_ids = {a['source_id'] for a in assignments}
    unmatched_entities = [
        {
            'id': str(row['id']),
            'name': row.get('name', 'Unknown'),
            'reason': 'No suitable match found'
        }
        for _, row in source_df.iterrows()
        if str(row['id']) not in matched_ids
    ]
    
    return {
        "proposed_assignments": matched,
        "unmatched_source": unmatched,
        "unmatched_target": len(target_df) - len(set(a['target_id'] for a in assignments)),
        "match_rate": round(match_rate, 2),
        "avg_match_score": round(avg_score, 2),
        "assignments_table": assignments[:50],  # Limit for preview
        "unmatched_entities": unmatched_entities[:20],
        "notification_count": len(params.notifications)
    }


async def _preview_monitoring(params: MonitoringParams) -> Dict[str, Any]:
    """Generate monitoring preview without sending alerts."""
    
    # Load data
    df = await load_data(params.source.entity_type, params.source.subtype)
    
    # Apply time-based filter
    flagged_df = filter_by_time_condition(
        df,
        params.condition.time_field,
        params.condition.threshold,
        params.condition.operator,
        params.condition.additional_filters
    )
    
    # Calculate days since for each flagged entity
    flagged_entities = []
    for _, row in flagged_df.head(50).iterrows():
        time_val = row.get(params.condition.time_field)
        if pd.notna(time_val):
            days_since = (datetime.now() - pd.to_datetime(time_val)).days
        else:
            days_since = None
        
        flagged_entities.append({
            'id': str(row['id']),
            'name': row.get('name', 'Unknown'),
            'last_contact': row.get('last_contact_date'),
            'days_since': days_since,
            'phone': row.get('phone'),
            'email': row.get('email')
        })
    
    avg_days = sum(e['days_since'] for e in flagged_entities if e['days_since']) / len(flagged_entities) if flagged_entities else 0
    
    return {
        "flagged_count": len(flagged_df),
        "avg_threshold_exceeded_by": f"{int(avg_days)} days",
        "flagged_entities": flagged_entities,
        "alert_recipients": [alert.recipient for alert in params.alerts],
        "optional_notification_count": len(params.optional_action.recipients) if params.optional_action else 0
    }


async def _preview_analysis(params: AnalysisParams) -> Dict[str, Any]:
    """Generate analysis preview without committing."""
    
    # Load data sources
    dfs = []
    for source in params.sources:
        df = await load_data(source.entity_type, source.subtype)
        if source.filters:
            df = filter_data(df, source.filters)
        dfs.append(df)
    
    # Merge if multiple sources and join_on specified
    if len(dfs) > 1 and params.join_on:
        merged_df = dfs[0]
        for df in dfs[1:]:
            merged_df = pd.merge(merged_df, df, on=params.join_on, how='inner')
    else:
        merged_df = dfs[0] if dfs else pd.DataFrame()
    
    # Calculate metrics
    metrics_result = calculate_metrics(params.metrics, merged_df)
    
    # Apply flag conditions if specified
    flagged_entities = []
    if params.flags:
        for flag_cond in params.flags:
            # Simple implementation - can be enhanced
            # For now, assume flag conditions are filter-compatible
            flagged_df = merged_df.head(20)  # Simplified for preview
            for _, row in flagged_df.iterrows():
                flagged_entities.append({
                    'id': str(row.get('id', '')),
                    'name': row.get('name', 'Unknown'),
                    'flag_reason': flag_cond.name
                })
    
    return {
        "metrics_summary": metrics_result,
        "flagged_entities": flagged_entities[:20],
        "notification_count": len(params.notifications),
        "dashboard_data": metrics_result  # Frontend can use this for visualization
    }


# ============================================================================
# TEMPLATE EXECUTORS (Actual execution with DB writes)
# ============================================================================

async def execute_matching(params: MatchingParams, workflow_run_id: str) -> Dict[str, Any]:
    """
    Execute matching workflow: load → filter → match → create assignments → notify.
    """
    
    # Step 1: Load data
    source_df = await load_data(params.source.entity_type, params.source.subtype)
    target_df = await load_data(params.target.entity_type, params.target.subtype)
    
    # Step 2: Filter
    if params.source.filters:
        source_df = filter_data(source_df, params.source.filters)
    if params.target.filters:
        target_df = filter_data(target_df, params.target.filters)
    
    # Step 3: Match
    assignments = match_func(
        source_df,
        target_df,
        params.match_strategy,
        params.match_fields,
        params.constraints
    )
    
    # Step 4: Create assignments in database
    assignment_records = [
        {
            "source_id": a['source_id'],
            "target_id": a['target_id'],
            "target_type": "group" if params.target.entity_type == EntityType.GROUP else "person",
            "assignment_type": f"{params.source.subtype}_to_{params.target.subtype}",
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
    for notif_config in params.notifications:
        
        # Determine recipients based on recipient_type
        if notif_config.recipient_type == "source":
            # Convert assignment IDs to strings for comparison
            source_ids = [str(a['source_id']) for a in assignments]
            # Convert DataFrame IDs to strings too
            recipients = source_df[source_df['id'].astype(str).isin(source_ids)].to_dict('records')
        elif notif_config.recipient_type in ["target", "target_owners"]:
            target_ids = [str(a['target_id']) for a in assignments]
            recipients = target_df[target_df['id'].astype(str).isin(target_ids)].to_dict('records')
        else:
            recipients = []
        
        if recipients:
            result = await send_notification(
                recipients,
                notif_config,
                global_variables={"count": len(assignments)},
                workflow_run_id=workflow_run_id
            )
            notification_results.append(result)
    
    # Calculate final metrics
    match_rate = len(assignments) / len(source_df) if len(source_df) > 0 else 0
    
    return {
        "assignments_created": len(assignments),
        "notifications_sent": sum(r['sent'] for r in notification_results),
        "match_rate": round(match_rate, 2),
        "total_source": len(source_df),
        "total_target": len(target_df)
    }


async def execute_monitoring(params: MonitoringParams, workflow_run_id: str) -> Dict[str, Any]:
    """
    Execute monitoring workflow: load → filter by time → send alerts.
    """
    
    # Step 1: Load data
    df = await load_data(params.source.entity_type, params.source.subtype)
    
    # Step 2: Filter by time condition
    flagged_df = filter_by_time_condition(
        df,
        params.condition.time_field,
        params.condition.threshold,
        params.condition.operator,
        params.condition.additional_filters
    )
    
    # Step 3: Send alerts to oversight team
    alert_results = []
    flagged_list = flagged_df.to_dict('records')
    
    for alert_config in params.alerts:
        # Send single alert to admin/pastor
        result = await send_notification(
            recipients=[{"id": "admin", "email": alert_config.recipient, "phone": alert_config.recipient}],
            config=alert_config,
            global_variables={
                "count": len(flagged_list),
                "names": ", ".join([r.get('name', 'Unknown') for r in flagged_list[:5]])
            },
            workflow_run_id=workflow_run_id
        )
        alert_results.append(result)
    
    # Step 4: Optional follow-up action
    followup_results = []
    if params.optional_action and params.optional_action.recipients == "flagged_entities":
        # Send to flagged entities themselves
        result = await send_notification(
            recipients=flagged_list,
            config=params.optional_action,
            workflow_run_id=workflow_run_id
        )
        followup_results.append(result)
    
    return {
        "flagged_count": len(flagged_df),
        "alerts_sent": sum(r['sent'] for r in alert_results),
        "followups_sent": sum(r['sent'] for r in followup_results),
        "total_notifications": sum(r['sent'] for r in alert_results + followup_results)
    }


async def execute_analysis(params: AnalysisParams, workflow_run_id: str) -> Dict[str, Any]:
    """
    Execute analysis workflow: load → join → calculate metrics → send reports.
    """
    
    # Step 1: Load data sources
    dfs = []
    for source in params.sources:
        df = await load_data(source.entity_type, source.subtype)
        if source.filters:
            df = filter_data(df, source.filters)
        dfs.append(df)
    
    # Step 2: Merge if needed
    if len(dfs) > 1 and params.join_on:
        merged_df = dfs[0]
        for df in dfs[1:]:
            merged_df = pd.merge(merged_df, df, on=params.join_on, how='inner')
    else:
        merged_df = dfs[0] if dfs else pd.DataFrame()
    
    # Step 3: Calculate metrics
    metrics_result = calculate_metrics(params.metrics, merged_df)
    
    # Step 4: Send notifications
    notification_results = []
    for notif_config in params.notifications:
        # For analysis, typically send to admin
        result = await send_notification(
            recipients=[{"id": "admin", "email": notif_config.recipient, "phone": notif_config.recipient}],
            config=notif_config,
            global_variables={"metrics": metrics_result},
            workflow_run_id=workflow_run_id
        )
        notification_results.append(result)
    
    return {
        "metrics": metrics_result,
        "rows_analyzed": len(merged_df),
        "notifications_sent": sum(r['sent'] for r in notification_results)
    }