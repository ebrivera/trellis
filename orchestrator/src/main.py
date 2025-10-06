from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from models import InterpretRequest, InterpretResponse, GoalSpec
from interpreter import interpret_goal
from database import init_db_pool, close_db_pool
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Church Orchestrator API", version="1.0.0")

@app.on_event("startup")
async def startup():
    """Initialize database connection pool on startup."""
    await init_db_pool()

@app.on_event("shutdown")
async def shutdown():
    """Close database connection pool on shutdown."""
    await close_db_pool()

@app.get("/")
def root():
    return {"status": "alive", "service": "orchestrator"}


@app.post("/goals/interpret", response_model=InterpretResponse)
def interpret_endpoint(request: InterpretRequest):
    """
    Convert natural language ask into a structured GoalSpec.
    
    Input:
        {
          "ask": "Place adults into groups near their ZIP and message them",
          "context": {...optional...}
        }
    
    Output:
        {
          "goalspec": { ... },
          "error": null
        }
    """
    try:
        goalspec = interpret_goal(request.ask, request.context)
        return InterpretResponse(goalspec=goalspec)
    
    except ValueError as e:
        return InterpretResponse(
            goalspec=None,
            error={"message": str(e), "type": "validation_error"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)