"""
FileCherry Orchestrator - Main entry point.

The orchestrator is the central controller that coordinates jobs,
manages state, and interfaces with services (Ollama, ComfyUI, doc processing).
"""

import os
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .inventory import InventoryScanner
from .manifest import ManifestManager
from .job import JobManager
from .planner import Planner
from .cody import cody_chat
from .models.cody_chat import CodyChatRequest, CodyChatResponse
from ..services.ollama_client import OllamaClient
from ..utils.logger import get_logger
from ..utils.security import ensure_secure_directory

# Get data directory from environment or default
DATA_DIR = Path(os.getenv("FILECHERRY_DATA_DIR", "/data"))
LOGS_DIR = DATA_DIR / "logs"

# Ensure log directory exists with secure permissions
ensure_secure_directory(LOGS_DIR, owner="filecherry")

# Configure structured logging
logger = get_logger("orchestrator", data_dir=DATA_DIR)

# Get data directory from environment or default
DATA_DIR = Path(os.getenv("FILECHERRY_DATA_DIR", "/data"))
INPUTS_DIR = DATA_DIR / "inputs"
OUTPUTS_DIR = DATA_DIR / "outputs"
RUNTIME_DIR = DATA_DIR / "runtime"
LOGS_DIR = DATA_DIR / "logs"

# Ensure directories exist
for dir_path in [DATA_DIR, INPUTS_DIR, OUTPUTS_DIR, RUNTIME_DIR, LOGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Initialize FastAPI app
app = FastAPI(
    title="FileCherry Orchestrator",
    description="Central orchestrator for FileCherry AI appliance",
    version="0.1.0",
)

# Add CORS middleware for UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
ollama_client = OllamaClient()
planner = Planner(ollama_client)

# Initialize components
inventory_scanner = InventoryScanner(INPUTS_DIR, RUNTIME_DIR)
manifest_manager = ManifestManager(OUTPUTS_DIR)
job_manager = JobManager(manifest_manager, planner=planner)


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    data_dir: str
    services: dict


class JobRequest(BaseModel):
    """Job creation request model."""

    intent: str
    user_id: Optional[str] = None


class JobResponse(BaseModel):
    """Job creation response model."""

    job_id: str
    status: str
    message: str


@app.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        data_dir=str(DATA_DIR),
        services={
            "inventory_scanner": "ready",
            "manifest_manager": "ready",
            "job_manager": "ready",
        },
    )


@app.get("/api/inventory")
async def get_inventory():
    """Get current inventory of files in inputs/."""
    try:
        inventory = inventory_scanner.scan()
        return JSONResponse(content=inventory)
    except Exception as e:
        logger.error(f"Error scanning inventory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/jobs", response_model=JobResponse)
async def create_job(request: JobRequest):
    """Create a new job from user intent."""
    try:
        # Scan current inventory
        inventory = inventory_scanner.scan()

        # Create job
        job_id = job_manager.create_job(request.intent, inventory)

        # Auto-start the job (planning and execution)
        try:
            job_manager.start_job(job_id)
        except Exception as e:
            logger.error(f"Error starting job {job_id}: {e}")
            # Job is created but failed to start - return it anyway

        return JobResponse(
            job_id=job_id,
            status="running",
            message=f"Job {job_id} created and started",
        )
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a specific job."""
    try:
        manifest = manifest_manager.load_manifest(job_id)
        if not manifest:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        return JSONResponse(content=manifest)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/{job_id}/manifest")
async def get_job_manifest(job_id: str):
    """Get full manifest for a job."""
    return await get_job_status(job_id)


@app.post("/api/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a running job."""
    try:
        job_manager.cancel_job(job_id)
        return JSONResponse(content={
            "job_id": job_id,
            "status": "cancelled",
            "message": f"Job {job_id} cancelled successfully",
        })
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error cancelling job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/cody/chat", response_model=CodyChatResponse)
async def chat_with_cody(request: CodyChatRequest):
    """Chat with Cody."""
    try:
        reply = await cody_chat(request.messages, ollama_client)
        return CodyChatResponse(reply=reply)
    except Exception as e:
        logger.error(f"Error in Cody chat: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Cody dropped a sack on that one: {str(e)}"
        )


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "FileCherry Orchestrator",
        "version": "0.1.0",
        "endpoints": {
            "health": "/healthz",
            "inventory": "/api/inventory",
            "create_job": "/api/jobs",
            "job_status": "/api/jobs/{job_id}",
            "job_manifest": "/api/jobs/{job_id}/manifest",
            "cody_chat": "/api/cody/chat",
        },
    }


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting FileCherry Orchestrator")
    logger.info(f"Data directory: {DATA_DIR}")
    uvicorn.run(app, host="0.0.0.0", port=8000)

