# orchestrator/src/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from .database import init_db_pool, close_db_pool, fetch_one, execute
from .graph import orchestrate_request, execute_workflow
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
    Main orchestration endpoint: NL request → classify → extract → approval gate.
    
    Frontend calls this from chat interface.
    Returns approval_id for frontend to show approval UI.
    """
    try:
        result = await orchestrate_request(
            request.request,
            request.available_files or []
        )
        
        return OrchestrateResponse(
            approvalId=result['approval_id'],
            workflowId=result['workflow_id'],
            template=result['template'],
            params=result['params'],
            preview=result.get('preview', {}),
            clarifications=result.get('clarifications', [])
        )
    
    except Exception as e:
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)