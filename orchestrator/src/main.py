# orchestrator/src/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from asyncio import Queue
import os
from dotenv import load_dotenv
import json
from typing import Optional, Dict, Any, List
from .database import init_db_pool, close_db_pool, fetch_one, execute
from .graph import run_orchestration
from .graph_executor import execute_workflow
from .graph_streaming import run_orchestration_with_events


load_dotenv()

app = FastAPI(title="Trellis Orchestrator API", version="1.0.0")

# Add CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class OrchestrateRequest(BaseModel):
    request: str = Field(..., description="Natural language request")
    csv_urls: Optional[Dict[str, str]] = Field(default=None, description="CSV file URLs (not used in MVP)")
    available_files: List[str] = Field(default_factory=list, description="Available CSV files")


class OrchestrateResponse(BaseModel):
    approval_id: str = Field(..., alias="approvalId")
    workflow_id: str = Field(..., alias="workflowId")
    template: str
    params: Dict[str, Any]
    preview: Dict[str, Any]
    clarifications: List[str] = Field(default_factory=list)
    
    class Config:
        populate_by_name = True


class ApprovalDecision(BaseModel):
    action: str = Field(..., description="'approve' or 'reject'")
    reason: Optional[str] = None


# Lifecycle
@app.on_event("startup")
async def startup():
    """Initialize database connection pool on startup."""
    await init_db_pool()
    print("✓ Orchestrator API started")


@app.on_event("shutdown")
async def shutdown():
    """Close database connection pool on shutdown."""
    await close_db_pool()


# Routes
@app.get("/")
def root():
    return {"status": "alive", "service": "trellis-orchestrator"}


@app.post("/orchestrate", response_model=OrchestrateResponse)
async def orchestrate(request: OrchestrateRequest):
    """
    Main orchestration endpoint: Multi-agent debate → approval gate.
    Frontend calls this from chat interface.
    """
    try:
        # Run the full debate orchestration
        result = await run_orchestration(
            request.request,
            request.available_files or []
        )
        
        return OrchestrateResponse(
            approvalId=result['approval_id'],
            workflowId=result['workflow_id'],
            template=result['template'].value,  # Convert enum to string
            params=result['debate_state']['params'],  # Params are nested in debate_state
            preview=result.get('preview', {}),
            clarifications=result.get('clarifications', [])
        )
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/approvals")
async def get_approvals(status: Optional[str] = None):
    """
    Get all approval gates, optionally filtered by status.

    Query params:
        status: Filter by status ('pending', 'saved', 'approved', 'rejected')
    """
    from .database import fetch_all

    if status:
        approvals = await fetch_all(
            """
            SELECT ag.*, wr.template_type, wr.request_text, wr.extracted_params
            FROM approval_gates ag
            JOIN workflow_runs wr ON ag.workflow_run_id = wr.id
            WHERE ag.status = $1
            ORDER BY ag.created_at DESC
            """,
            status
        )
    else:
        approvals = await fetch_all(
            """
            SELECT ag.*, wr.template_type, wr.request_text, wr.extracted_params
            FROM approval_gates ag
            JOIN workflow_runs wr ON ag.workflow_run_id = wr.id
            ORDER BY ag.created_at DESC
            """
        )

    return {"approvals": approvals}


@app.get("/approval/{approval_id}")
async def get_approval(approval_id: str):
    """
    Get approval gate details for frontend approval UI.
    Includes extracted_params from workflow_run.
    """
    approval = await fetch_one(
        """
        SELECT ag.*, wr.template_type, wr.request_text, wr.extracted_params
        FROM approval_gates ag
        JOIN workflow_runs wr ON ag.workflow_run_id = wr.id
        WHERE ag.id = $1
        """,
        approval_id
    )

    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    return approval


class UpdateApprovalStatus(BaseModel):
    status: str = Field(..., description="New status: 'pending', 'saved', 'approved', 'rejected'")


@app.patch("/approval/{approval_id}")
async def update_approval_status(approval_id: str, update: UpdateApprovalStatus):
    """
    Update approval gate status (e.g., mark as 'saved' for later review).
    """
    approval = await fetch_one(
        "SELECT * FROM approval_gates WHERE id = $1",
        approval_id
    )

    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    # Update status
    await execute(
        "UPDATE approval_gates SET status = $1 WHERE id = $2",
        update.status, approval_id
    )

    return {
        "status": "success",
        "message": f"Approval status updated to '{update.status}'"
    }


@app.post("/approval/{approval_id}/decide")
async def decide_approval(approval_id: str, decision: ApprovalDecision):
    """
    Handle approval decision: approve or reject.
    
    If approved: execute the workflow (create assignments, send notifications).
    If rejected: mark as rejected and stop.
    """
    approval = await fetch_one(
        "SELECT * FROM approval_gates WHERE id = $1",
        approval_id
    )
    
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    if decision.action == "approve":
        # Update approval status
        await execute(
            "UPDATE approval_gates SET status = $1, approved_at = NOW() WHERE id = $2",
            "approved", approval_id
        )

        # Execute workflow
        try:
            result = await execute_workflow(approval_id)

            return {
                "status": "approved",
                "message": "Workflow executed successfully",
                "workflow_id": approval['workflow_run_id'],
                "result": result
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")
    
    elif decision.action == "reject":
        await execute(
            "UPDATE approval_gates SET status = $1, approved_at = NOW(), rejection_reason = $2 WHERE id = $3",
            "rejected", decision.reason or "User rejected", approval_id
        )
        
        # Update workflow run status
        workflow_run_id = approval['workflow_run_id']
        await execute(
            "UPDATE workflow_runs SET status = $1 WHERE id = $2",
            "rejected", workflow_run_id
        )
        
        return {
            "status": "rejected",
            "message": "Workflow cancelled"
        }
    
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Must be 'approve' or 'reject'")

@app.get("/orchestrate/stream")
async def orchestrate_stream(request: str):
    """
    Streaming version of orchestrate endpoint.
    Sends SSE events as debate progresses in real-time.
    """
    
    async def event_generator():
        """Generator that yields SSE events in real-time"""
        import asyncio
        
        try:
            # Create a queue to collect events
            event_queue = Queue()
            
            # Flag to track when orchestration is done
            orchestration_done = False
            result = None
            error = None
            
            # Run orchestration in background task
            async def run_in_background():
                nonlocal orchestration_done, result, error
                try:
                    result = await run_orchestration_with_events(
                        request,  
                        [],    
                        event_queue
                    )
                except Exception as e:
                    error = e
                finally:
                    orchestration_done = True
            
            # Start background task
            task = asyncio.create_task(run_in_background())
            
            # Yield events as they arrive in queue
            while not orchestration_done or not event_queue.empty():
                try:
                    # Wait for event with timeout to check if done
                    event = await asyncio.wait_for(event_queue.get(), timeout=0.1)
                    
                    # Format and yield as SSE
                    yield f"event: {event['event']}\n"
                    yield f"data: {json.dumps(event['data'])}\n\n"
                    
                except asyncio.TimeoutError:
                    # No event available, check if we should continue waiting
                    if orchestration_done and event_queue.empty():
                        break
                    continue
            
            # Wait for background task to complete
            await task
            
            # Check for errors
            if error:
                raise error
            
            # Send final completion event
            yield f"event: complete\n"
            yield f"data: {json.dumps({'status': 'success'})}\n\n"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            
            # Send error event
            yield f"event: error\n"
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
# ============================================================================
# DASHBOARD OVERVIEW
# ============================================================================

@app.get("/dashboard/overview")
async def get_dashboard_overview():
    """
    Get all overview card data in one call.
    
    Returns:
        - card1: Pending Approvals count
        - card2: Completed Workflows (last 7 days)
        - card3: Messages Queued count
        - card4: Total statistics (messages sent, workflows run, assignments made)
    """
    from .database import fetch_one
    
    # Card 1: Pending Approvals
    card1 = await fetch_one(
        "SELECT COUNT(*) as count FROM approval_gates WHERE status = 'pending'"
    )
    
    # Card 2: Completed Workflows (Last 7 Days)
    card2 = await fetch_one(
        "SELECT COUNT(*) as count FROM workflow_runs "
        "WHERE status = 'completed' "
        "AND completed_at >= CURRENT_DATE - INTERVAL '7 days'"
    )
    
    # Card 3: Messages Queued
    card3 = await fetch_one(
        "SELECT COUNT(*) as count FROM messages WHERE status = 'queued'"
    )
    
    # Card 4: Statistics (3 metrics)
    total_messages_sent = await fetch_one(
        "SELECT COUNT(*) as count FROM messages WHERE status = 'sent'"
    )
    
    total_workflows = await fetch_one(
        "SELECT COUNT(*) as count FROM workflow_runs"
    )
    
    total_assignments = await fetch_one(
        "SELECT COUNT(*) as count FROM assignments"
    )
    
    return {
        "card1": {
            "label": "Pending Approvals",
            "value": card1['count']
        },
        "card2": {
            "label": "Completed Workflows",
            "sublabel": "Last 7 Days",
            "value": card2['count']
        },
        "card3": {
            "label": "Messages Queued",
            "value": card3['count']
        },
        "card4": {
            "label": "Statistics",
            "stats": [
                {
                    "label": "Messages Sent",
                    "value": total_messages_sent['count']
                },
                {
                    "label": "Workflows Run",
                    "value": total_workflows['count']
                },
                {
                    "label": "Assignments Made",
                    "value": total_assignments['count']
                }
            ]
        }
    }


# ============================================================================
# RECENT ACTIVITY (DASHBOARD)
# ============================================================================

@app.get("/dashboard/recent-activity")
async def get_recent_activity():
    from .database import fetch_all
    
    # Get recent workflow runs, approval decisions, and assignments
    activities = await fetch_all("""
        SELECT 
            'workflow' as activity_type,
            id,
            template_type,
            status,
            request_text,
            created_at AT TIME ZONE 'UTC' as created_at,
            completed_at AT TIME ZONE 'UTC' as completed_at
        FROM workflow_runs
        WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
        AND status != 'awaiting_approval'
        
        UNION ALL
        
        SELECT 
            'approval' as activity_type,
            ag.id,
            ag.gate_type as template_type,
            ag.status,
            wr.request_text,
            ag.created_at AT TIME ZONE 'UTC' as created_at,
            ag.approved_at AT TIME ZONE 'UTC' as completed_at
        FROM approval_gates ag
        JOIN workflow_runs wr ON ag.workflow_run_id = wr.id
        WHERE ag.created_at >= CURRENT_DATE - INTERVAL '7 days'
        
        ORDER BY created_at DESC
        LIMIT 5
    """)
    
    return {"activities": activities}


# ============================================================================
# MONTHLY METRICS (DASHBOARD)
# ============================================================================

@app.get("/dashboard/monthly-metrics")
async def get_monthly_metrics():
    from .database import fetch_one

    # Workflows completed this month vs last month
    workflows_this_month = await fetch_one("""
        SELECT COUNT(*) as count
        FROM workflow_runs
        WHERE status = 'completed'
        AND completed_at >= DATE_TRUNC('month', CURRENT_DATE)
    """)

    workflows_last_month = await fetch_one("""
        SELECT COUNT(*) as count
        FROM workflow_runs
        WHERE status = 'completed'
        AND completed_at >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
        AND completed_at < DATE_TRUNC('month', CURRENT_DATE)
    """)

    # Assignments created this month vs last month
    assignments_this_month = await fetch_one("""
        SELECT COUNT(*) as count
        FROM assignments
        WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)
    """)

    assignments_last_month = await fetch_one("""
        SELECT COUNT(*) as count
        FROM assignments
        WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
        AND created_at < DATE_TRUNC('month', CURRENT_DATE)
    """)

    # Messages sent this month vs last month
    messages_this_month = await fetch_one("""
        SELECT COUNT(*) as count
        FROM messages
        WHERE status = 'sent'
        AND created_at >= DATE_TRUNC('month', CURRENT_DATE)
    """)

    messages_last_month = await fetch_one("""
        SELECT COUNT(*) as count
        FROM messages
        WHERE status = 'sent'
        AND created_at >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
        AND created_at < DATE_TRUNC('month', CURRENT_DATE)
    """)

    return {
        "metrics": [
            {
                "label": "Workflows Completed",
                "current": workflows_this_month['count'],
                "previous": workflows_last_month['count'],
                "change": workflows_this_month['count'] - workflows_last_month['count']
            },
            {
                "label": "Assignments Created",
                "current": assignments_this_month['count'],
                "previous": assignments_last_month['count'],
                "change": assignments_this_month['count'] - assignments_last_month['count']
            },
            {
                "label": "Messages Sent",
                "current": messages_this_month['count'],
                "previous": messages_last_month['count'],
                "change": messages_this_month['count'] - messages_last_month['count']
            }
        ]
    }


# ============================================================================
# WORKFLOW RESULTS
# ============================================================================

@app.get("/workflow/{workflow_id}")
async def get_workflow_result(workflow_id: str):
    """
    Get workflow execution results with full context.

    Returns:
        - Original request
        - Template type
        - Winning agent and strategy
        - Execution results and metrics
        - Actions taken (assignments, notifications)
    """
    from .database import fetch_all

    # Fetch workflow run
    workflow = await fetch_one(
        """
        SELECT wr.*, ag.status as approval_status
        FROM workflow_runs wr
        LEFT JOIN approval_gates ag ON ag.workflow_run_id = wr.id
        WHERE wr.id = $1
        """,
        workflow_id
    )

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Parse extracted_params to get winning strategy
    extracted_params = workflow['extracted_params']
    if isinstance(extracted_params, str):
        extracted_params = json.loads(extracted_params)

    # Parse results
    results = workflow['results']
    if isinstance(results, str):
        results = json.loads(results) if results else {}

    # Fetch all people affected by this workflow with their actions
    # This combines assignments and messages into a person-centric view

    # Debug: Check if messages exist
    print(f"🔍 DEBUG: Fetching affected people for workflow {workflow_id}")
    message_count = await fetch_one(
        "SELECT COUNT(*) as count FROM messages WHERE workflow_run_id = $1",
        workflow_id
    )
    print(f"🔍 DEBUG: Found {message_count['count']} messages for this workflow")

    affected_people = await fetch_all(
        """
        WITH workflow_people AS (
            -- People who received assignments
            SELECT DISTINCT
                p.id::text as id,
                p.name,
                p.email,
                p.phone,
                p.person_type
            FROM assignments a
            JOIN people p ON a.source_id = p.id
            WHERE a.workflow_run_id = $1

            UNION

            -- People who received messages
            SELECT DISTINCT
                p.id::text as id,
                p.name,
                p.email,
                p.phone,
                p.person_type
            FROM messages m
            JOIN people p ON m.recipient_id::uuid = p.id
            WHERE m.workflow_run_id = $1
        )
        SELECT
            wp.*,
            -- Get their assignments
            COALESCE(
                json_agg(
                    DISTINCT jsonb_build_object(
                        'assigned_to', COALESCE(p2.name, g.name),
                        'assignment_type', a.assignment_type,
                        'match_score', a.match_score,
                        'status', a.status
                    )
                ) FILTER (WHERE a.id IS NOT NULL),
                '[]'
            ) as assignments,
            -- Get their messages
            COALESCE(
                json_agg(
                    DISTINCT jsonb_build_object(
                        'channel', m.channel,
                        'status', m.status,
                        'template', m.template,
                        'sent_at', m.sent_at
                    )
                ) FILTER (WHERE m.id IS NOT NULL),
                '[]'
            ) as messages
        FROM workflow_people wp
        LEFT JOIN assignments a ON a.source_id::uuid = wp.id::uuid AND a.workflow_run_id = $1
        LEFT JOIN people p2 ON a.target_id = p2.id AND a.target_type = 'person'
        LEFT JOIN groups g ON a.target_id = g.id AND a.target_type = 'group'
        LEFT JOIN messages m ON m.recipient_id::uuid = wp.id::uuid AND m.workflow_run_id = $1
        GROUP BY wp.id, wp.name, wp.email, wp.phone, wp.person_type
        ORDER BY wp.name
        """,
        workflow_id
    )

    print(f"🔍 DEBUG: Found {len(affected_people)} affected people")
    if len(affected_people) > 0:
        print(f"🔍 DEBUG: First person: {affected_people[0]}")
    else:
        print(f"🔍 DEBUG: No affected people found - checking messages table directly...")
        sample_messages = await fetch_all(
            "SELECT id, recipient_id, workflow_run_id FROM messages WHERE workflow_run_id = $1 LIMIT 3",
            workflow_id
        )
        print(f"🔍 DEBUG: Sample messages: {sample_messages}")

    return {
        "id": workflow['id'],
        "request": workflow['request_text'],
        "template": workflow['template_type'],
        "status": workflow['status'],
        "winning_agent": extracted_params.get('winning_agent', 'Unknown'),
        "winning_strategy": extracted_params.get('winning_strategy', ''),
        "results": results,
        "affected_people": affected_people,
        "created_at": workflow['started_at'],
        "completed_at": workflow['completed_at']
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)