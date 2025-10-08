# orchestrator/src/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from .database import init_db_pool, close_db_pool, fetch_one, execute
from .graph import run_orchestration
from .graph_executor import execute_workflow
import os
from dotenv import load_dotenv

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


@app.get("/approval/{approval_id}")
async def get_approval(approval_id: str):
    """
    Get approval gate details for frontend approval UI.
    """
    approval = await fetch_one(
        "SELECT * FROM approval_gates WHERE id = $1",
        approval_id
    )
    
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    return approval


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
            created_at,
            completed_at
        FROM workflow_runs
        WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
        
        UNION ALL
        
        SELECT 
            'approval' as activity_type,
            ag.id,
            ag.gate_type as template_type,
            ag.status,
            wr.request_text,
            ag.created_at,
            ag.approved_at as completed_at
        FROM approval_gates ag
        JOIN workflow_runs wr ON ag.workflow_run_id = wr.id
        WHERE ag.created_at >= CURRENT_DATE - INTERVAL '7 days'
        
        ORDER BY created_at DESC
        LIMIT 10
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)