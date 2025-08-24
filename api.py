#!/usr/bin/env python3
"""
Universal Web Action Agent - FastAPI Endpoint

This module provides a REST API for the web automation system.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add the core module to the path
sys.path.insert(0, str(Path(__file__).parent))

from core.agent import UniversalWebAgent, AgentConfig
from core.exceptions import WebAutomationError


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Pydantic models for API requests/responses
class TaskRequest(BaseModel):
    """Request model for task execution."""
    instruction: str
    headless: bool = False
    timeout: int = 30000


class TaskResponse(BaseModel):
    """Response model for task execution."""
    success: bool
    task: Dict[str, Any] = {}
    results: Dict[str, Any] = {}
    logs: list = []
    error: str = ""


# Initialize FastAPI app
app = FastAPI(
    title="Universal Web Action Agent API",
    description="AI-powered web automation system",
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


def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    config = {}
    
    # Try to load from .env file
    env_file = Path('.env')
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv()
    
    # Load from environment variables
    config['openai_api_key'] = os.getenv('OPENAI_API_KEY')
    config['headless'] = os.getenv('HEADLESS', 'false').lower() == 'true'
    config['timeout'] = int(os.getenv('TIMEOUT', '30000'))
    config['log_level'] = os.getenv('LOG_LEVEL', 'INFO')
    
    return config


def validate_config(config: Dict[str, Any]) -> None:
    """Validate that required configuration is present."""
    if not config.get('openai_api_key'):
        raise ValueError("OPENAI_API_KEY environment variable is required")


@app.on_event("startup")
async def startup_event():
    """Initialize the system on startup."""
    try:
        config = load_config()
        validate_config(config)
        logger.info("Configuration validated successfully")
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        raise


@app.get("/")
async def root():
    """Root endpoint with system information."""
    return {
        "name": "Universal Web Action Agent API",
        "version": "1.0.0",
        "description": "AI-powered web automation system",
        "endpoints": {
            "/": "This information",
            "/health": "System health check",
            "/execute": "Execute a web automation task",
            "/docs": "API documentation (Swagger UI)"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Basic health check
        config = load_config()
        validate_config(config)
        
        return {
            "status": "healthy",
            "config": {
                "openai_api_key_configured": bool(config.get('openai_api_key')),
                "headless": config.get('headless'),
                "timeout": config.get('timeout'),
                "log_level": config.get('log_level')
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.post("/execute")
async def execute_task(request: TaskRequest) -> TaskResponse:
    """Execute a web automation task."""
    try:
        # Load configuration
        config = load_config()
        validate_config(config)
        
        # Override config with request parameters
        if request.headless is not None:
            config['headless'] = request.headless
        if request.timeout is not None:
            config['timeout'] = request.timeout
        
        # Create agent configuration
        agent_config = AgentConfig(
            openai_api_key=config['openai_api_key'],
            headless=config['headless'],
            timeout=config['timeout'],
            log_level=config['log_level']
        )
        
        # Initialize the agent
        logger.info("Initializing Universal Web Action Agent...")
        agent = UniversalWebAgent(agent_config)
        
        # Set up credentials for providers
        gmail_email = os.getenv('GMAIL_EMAIL')
        gmail_password = os.getenv('GMAIL_PASSWORD')
        outlook_email = os.getenv('OUTLOOK_EMAIL')
        outlook_password = os.getenv('OUTLOOK_PASSWORD')
        
        if gmail_email and gmail_password:
            agent.providers['gmail'].set_credentials({
                'email': gmail_email,
                'password': gmail_password
            })
            logger.info("Gmail credentials configured")
            
        if outlook_email and outlook_password:
            agent.providers['outlook'].set_credentials({
                'email': outlook_email,
                'password': outlook_password
            })
            logger.info("Outlook credentials configured")
        
        # Execute the task
        logger.info(f"Executing task: {request.instruction}")
        result = await agent.execute_task(request.instruction)
        
        # Clean up
        await agent.close()
        
        # Return response
        return TaskResponse(
            success=result.get("success", False),
            task=result.get("task", {}),
            results=result.get("results", {}),
            logs=result.get("logs", []),
            error=result.get("error", "")
        )
        
    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        return TaskResponse(
            success=False,
            error=str(e),
            logs=[f"Error: {str(e)}"]
        )


@app.get("/providers")
async def list_providers():
    """List available service providers."""
    return {
        "providers": [
            {
                "name": "gmail",
                "description": "Gmail web interface automation",
                "supported_tasks": ["send_email", "compose_email", "reply_email"]
            },
            {
                "name": "outlook",
                "description": "Outlook web interface automation",
                "supported_tasks": ["send_email", "compose_email", "reply_email"]
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    
    # Load configuration for server startup
    try:
        config = load_config()
        validate_config(config)
        
        # Start the server
        uvicorn.run(
            "api:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
