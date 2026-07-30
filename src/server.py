"""Simple HTTP server for LangGraph without Docker."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure project root is in path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import json
from typing import Any

from src.graph import get_graph
from src.utils import get_settings, SOCWorkflowState

# Initialize FastAPI app
app = FastAPI(
    title="SecureOps AI - Local Agent Server",
    description="HTTP server for LangGraph agent execution",
    version="1.0.0",
)

# Store graph instance
graph = get_graph()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "SecureOps AI Agent Server",
        "version": "1.0.0",
    }


@app.post("/invoke")
async def invoke_graph(request: Request):
    """Execute the graph with input state."""
    try:
        body = await request.json()
        user_message = body.get("user_message", "")
        conversation_history = body.get("conversation_history", [])

        if not user_message:
            return JSONResponse(
                status_code=400,
                content={"error": "user_message is required"},
            )

        # Create initial state
        initial_state: SOCWorkflowState = {
            "user_message": user_message,
            "conversation_history": conversation_history,
            "request_info": {},
            "requested_actions": [],
            "completed_actions": [],
            "alert_analysis": None,
            "identity": None,
            "endpoint": None,
            "incident": None,
            "reporting": None,
            "final_response": None,
        }

        # Invoke graph
        result = graph.invoke(initial_state)

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "result": {
                    "final_response": result.get("final_response"),
                    "request_info": result.get("request_info"),
                    "completed_actions": result.get("completed_actions"),
                },
            },
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
            },
        )


@app.get("/graph")
async def get_graph_info():
    """Get graph schema and structure information."""
    try:
        # Return graph structure for visualization
        return JSONResponse(
            status_code=200,
            content={
                "name": "SecureOps AI SOC Assistant",
                "description": "Multi-agent workflow for security operations",
                "nodes": [
                    "request_intake",
                    "supervisor",
                    "alert_analysis",
                    "identity",
                    "endpoint",
                    "incident",
                    "reporting",
                    "response_generator",
                ],
                "edges": [
                    {"source": "request_intake", "target": "supervisor"},
                    {"source": "supervisor", "target": "response_generator"},
                ],
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )


@app.get("/")
async def root():
    """Root endpoint with API documentation."""
    return {
        "service": "SecureOps AI - Local Agent Server",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "graph_info": "/graph",
            "invoke": "/invoke (POST)",
        },
        "usage": {
            "invoke_example": {
                "method": "POST",
                "url": "http://localhost:8000/invoke",
                "body": {
                    "user_message": "Check alert severity for alert ID 123",
                    "conversation_history": [],
                },
            },
        },
        "connect_to_studio": {
            "instructions": [
                "1. Open LangSmith Studio",
                "2. Click 'Configure Studio connection'",
                "3. Enter Base URL: http://localhost:8000",
                "4. Click 'Connect'",
            ],
        },
    }


def main():
    """Start the server."""
    settings = get_settings()

    print()
    print("=" * 60)
    print("  SecureOps AI - Local Agent Server")
    print("=" * 60)
    print()
    print("Server Configuration:")
    print(f"  Host: 127.0.0.1")
    print(f"  Port: 8000")
    print(f"  URL: http://localhost:8000")
    print()
    print("LangSmith Configuration:")
    print(f"  Project: {settings.langsmith_project}")
    print(f"  Endpoint: {settings.langsmith_endpoint}")
    print(f"  Tracing: {'Enabled' if settings.langsmith_tracing else 'Disabled'}")
    print()
    print("How to connect to LangSmith Studio:")
    print("  1. Open LangSmith Studio")
    print("  2. Click 'Configure Studio connection'")
    print("  3. Enter Base URL: http://localhost:8000")
    print("  4. Click 'Connect'")
    print()
    print("API Endpoints:")
    print("  GET  http://localhost:8000/          - API info")
    print("  GET  http://localhost:8000/health    - Health check")
    print("  GET  http://localhost:8000/graph     - Graph structure")
    print("  POST http://localhost:8000/invoke    - Execute graph")
    print()
    print("=" * 60)
    print()

    # Start server
    uvicorn.run(
        "src.server:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
