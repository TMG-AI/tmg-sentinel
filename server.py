"""
TMG Vetting Pipeline — API Server
===================================
FastAPI server that connects the Lovable dashboard to the Python pipeline.
Lovable submits a vetting → server runs pipeline in background → Lovable polls for results.

Run with: uvicorn server:app --reload --port 8000
"""

import json
import uuid
import threading
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

import config

# Import pipeline runner (add scripts/ to path)
import sys
sys.path.insert(0, str(config.SCRIPTS_DIR))
from pipeline import run_pipeline

app = FastAPI(title="TMG Vetting Pipeline API", version="1.0")

# Allow Lovable frontend to call this API (localhost + deployed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your Lovable domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── In-memory job tracker ──────────────────────────────
# Tracks pipeline runs: {vetting_id: {status, progress, result}}
jobs: dict = {}


# ─── Request/Response Models ────────────────────────────

class VettingSubmission(BaseModel):
    subject_name: str
    subject_type: str = "individual"
    company_affiliation: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    brief_bio: Optional[str] = None
    referral_source: Optional[str] = None
    engagement_type: str = "domestic_corporate"
    vetting_level: str = "standard_vet"
    requested_by: str = "Shannon"


class VettingStatus(BaseModel):
    id: str
    status: str  # pending, running, completed, gates_failed, error
    current_step: Optional[str] = None
    result_json: Optional[dict] = None
    error: Optional[str] = None


# ─── Background Pipeline Runner ─────────────────────────

def _run_pipeline_background(vetting_id: str, submission: VettingSubmission):
    """Run the full pipeline in a background thread."""
    try:
        jobs[vetting_id]["status"] = "running"
        jobs[vetting_id]["current_step"] = "Starting pipeline..."

        result = run_pipeline(
            name=submission.subject_name,
            subject_type=submission.subject_type,
            company=submission.company_affiliation,
            country=submission.country,
            city=submission.city,
            brief_bio=submission.brief_bio,
            referral_source=submission.referral_source,
            engagement_type=submission.engagement_type,
            vetting_level=submission.vetting_level,
            requested_by=submission.requested_by,
        )

        # Load the unified JSON (the full result for Lovable)
        subject_id = result.get("subject_id", vetting_id)
        unified_path = config.UNIFIED_DIR / f"{subject_id}.json"

        if unified_path.exists():
            with open(unified_path) as f:
                result_json = json.load(f)
            jobs[vetting_id]["result_json"] = result_json
            jobs[vetting_id]["status"] = result.get("status", "completed")
        else:
            # Gates failed or error — no unified JSON produced
            jobs[vetting_id]["status"] = result.get("status", "error")

        jobs[vetting_id]["current_step"] = None
        jobs[vetting_id]["pipeline_summary"] = result

    except Exception as e:
        jobs[vetting_id]["status"] = "error"
        jobs[vetting_id]["error"] = str(e)
        jobs[vetting_id]["current_step"] = None


# ─── API Endpoints ──────────────────────────────────────

@app.post("/api/vettings", response_model=VettingStatus)
def submit_vetting(submission: VettingSubmission):
    """Submit a new vetting. Kicks off pipeline in background."""
    vetting_id = str(uuid.uuid4())[:8]

    jobs[vetting_id] = {
        "status": "pending",
        "current_step": None,
        "result_json": None,
        "error": None,
        "submission": submission.model_dump(),
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }

    # Run pipeline in background thread
    thread = threading.Thread(
        target=_run_pipeline_background,
        args=(vetting_id, submission),
        daemon=True,
    )
    thread.start()

    return VettingStatus(id=vetting_id, status="running")


@app.get("/api/vettings/{vetting_id}", response_model=VettingStatus)
def get_vetting(vetting_id: str):
    """Get vetting status and results. Lovable polls this until complete."""
    if vetting_id not in jobs:
        raise HTTPException(status_code=404, detail="Vetting not found")

    job = jobs[vetting_id]
    return VettingStatus(
        id=vetting_id,
        status=job["status"],
        current_step=job.get("current_step"),
        result_json=job.get("result_json"),
        error=job.get("error"),
    )


@app.get("/api/vettings")
def list_vettings():
    """List all vettings with basic info."""
    return [
        {
            "id": vid,
            "status": job["status"],
            "subject_name": job["submission"]["subject_name"],
            "submitted_at": job.get("submitted_at"),
            "has_results": job.get("result_json") is not None,
        }
        for vid, job in jobs.items()
    ]


@app.get("/api/health")
def health():
    """Health check — Lovable Settings page can ping this."""
    keys_ok = config.verify_keys()
    return {
        "status": "ok",
        "api_keys_configured": keys_ok,
        "active_jobs": sum(1 for j in jobs.values() if j["status"] == "running"),
        "total_jobs": len(jobs),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
