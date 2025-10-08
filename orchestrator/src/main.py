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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)