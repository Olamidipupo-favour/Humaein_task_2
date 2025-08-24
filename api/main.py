"""
FastAPI Endpoint for Universal Web Action Agent

This module provides a REST API interface for the web automation system,
allowing programmatic access to the agent's capabilities.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Add the core module to the path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent import UniversalWebAgent, AgentConfig
from core.exceptions import WebAutomationError


# Pydantic models for API requests/responses
class TaskRequest(BaseModel):
    """Request model for task execution."""
    
    instruction: str = Field(..., description="Natural language instruction describing the task")
    providers: Optional[list] = Field(default=None, description="Specific providers to use")
    headless: bool = Field(default=True, description="Run browser in headless mode")
    timeout: int = Field(default=30000, description="Browser timeout in milliseconds")


class TaskResponse(BaseModel):
    """Response model for task execution."""
    
    task_id: str = Field(..., description="Unique identifier for the task")
    status: str = Field(..., description="Current status of the task")
    instruction: str = Field(..., description="The original instruction")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Task execution result")
    error: Optional[str] = Field(default=None, description="Error message if task failed")


class TaskStatus(BaseModel):
    """Model for task status information."""
    
    task_id: str = Field(..., description="Unique identifier for the task")
    status: str = Field(..., description="Current status of the task")
    progress: float = Field(default=0.0, description="Progress percentage (0-100)")
    message: str = Field(..., description="Current status message")
    created_at: str = Field(..., description="Task creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


# Global variables for task management
app = FastAPI(
    title="Universal Web Action Agent API",
    description="REST API for executing web automation tasks across multiple service providers",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Task storage (in production, use a proper database)
tasks: Dict[str, Dict[str, Any]] = {}
task_counter = 0

# Global agent instance
agent: Optional[UniversalWebAgent] = None


def get_agent() -> UniversalWebAgent:
    """Get or create the global agent instance."""
    global agent
    if agent is None:
        # Load configuration from environment
        import os
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            raise HTTPException(
                status_code=500,
                detail="OPENAI_API_KEY environment variable not set"
            )
            
        config = AgentConfig(
            openai_api_key=openai_api_key,
            headless=True,
            timeout=30000,
            log_level="INFO"
        )
        
        agent = UniversalWebAgent(config)
        
        # Set up credentials if available
        gmail_email = os.getenv('GMAIL_EMAIL')
        gmail_password = os.getenv('GMAIL_PASSWORD')
        outlook_email = os.getenv('OUTLOOK_EMAIL')
        outlook_password = os.getenv('OUTLOOK_PASSWORD')
        
        if gmail_email and gmail_password:
            agent.providers['gmail'].set_credentials({
                'email': gmail_email,
                'password': gmail_password
            })
            
        if outlook_email and outlook_password:
            agent.providers['outlook'].set_credentials({
                'email': outlook_email,
                'password': outlook_password
            })
            
    return agent


async def execute_task_background(task_id: str, request: TaskRequest) -> None:
    """Execute a task in the background."""
    try:
        # Update task status
        tasks[task_id]["status"] = "running"
        tasks[task_id]["message"] = "Task execution started"
        tasks[task_id]["updated_at"] = get_timestamp()
        
        # Get agent and execute task
        agent = get_agent()
        result = await agent.execute_task(request.instruction)
        
        # Update task with result
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["result"] = result
        tasks[task_id]["message"] = "Task completed successfully"
        tasks[task_id]["progress"] = 100.0
        tasks[task_id]["updated_at"] = get_timestamp()
        
    except Exception as e:
        # Update task with error
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)
        tasks[task_id]["message"] = f"Task failed: {e}"
        tasks[task_id]["updated_at"] = get_timestamp()
        
        logging.error(f"Task {task_id} failed: {e}")


def get_timestamp() -> str:
    """Get current timestamp as string."""
    from datetime import datetime
    return datetime.now().isoformat()


def generate_task_id() -> str:
    """Generate a unique task ID."""
    global task_counter
    task_counter += 1
    return f"task_{task_counter}_{int(asyncio.get_event_loop().time())}"


@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    logging.basicConfig(level=logging.INFO)
    logging.info("Universal Web Action Agent API starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    global agent
    if agent:
        await agent.close()
        logging.info("Agent resources cleaned up")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Universal Web Action Agent API",
        "version": "1.0.0",
        "endpoints": {
            "POST /tasks": "Submit a new task for execution",
            "GET /tasks/{task_id}": "Get task status and results",
            "GET /tasks": "List all tasks",
            "GET /providers": "Get available service providers",
            "GET /health": "Health check endpoint"
        }
    }


@app.post("/tasks", response_model=TaskResponse)
async def create_task(request: TaskRequest, background_tasks: BackgroundTasks):
    """Create and submit a new task for execution."""
    try:
        # Generate unique task ID
        task_id = generate_task_id()
        
        # Create task record
        tasks[task_id] = {
            "task_id": task_id,
            "status": "pending",
            "instruction": request.instruction,
            "progress": 0.0,
            "message": "Task created and queued for execution",
            "created_at": get_timestamp(),
            "updated_at": get_timestamp(),
            "result": None,
            "error": None
        }
        
        # Add task to background execution
        background_tasks.add_task(execute_task_background, task_id, request)
        
        return TaskResponse(
            task_id=task_id,
            status="pending",
            instruction=request.instruction
        )
        
    except Exception as e:
        logging.error(f"Failed to create task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/{task_id}", response_model=TaskStatus)
async def get_task(task_id: str):
    """Get the status and results of a specific task."""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
        
    task = tasks[task_id]
    return TaskStatus(**task)


@app.get("/tasks")
async def list_tasks():
    """List all tasks with their status."""
    return {
        "tasks": [
            {
                "task_id": task["task_id"],
                "status": task["status"],
                "instruction": task["instruction"],
                "created_at": task["created_at"],
                "updated_at": task["updated_at"]
            }
            for task in tasks.values()
        ],
        "total": len(tasks)
    }


@app.get("/providers")
async def get_providers():
    """Get information about available service providers."""
    try:
        agent = get_agent()
        providers_info = {}
        
        for name, provider in agent.providers.items():
            providers_info[name] = {
                "name": provider.name,
                "supported_tasks": provider.get_supported_tasks(),
                "has_credentials": provider.validate_credentials()
            }
            
        return {
            "providers": providers_info,
            "total": len(providers_info)
        }
        
    except Exception as e:
        logging.error(f"Failed to get providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Try to get agent (this will test configuration)
        agent = get_agent()
        return {
            "status": "healthy",
            "agent_initialized": True,
            "timestamp": get_timestamp()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "agent_initialized": False,
            "error": str(e),
            "timestamp": get_timestamp()
        }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
