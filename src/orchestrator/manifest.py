"""
Job manifest management.

Creates and manages job manifests that track job state,
steps, inputs, outputs, and metadata.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ManifestManager:
    """Manages job manifests stored in outputs/<job-id>/manifest.json."""

    def __init__(self, outputs_dir: Path):
        """Initialize manifest manager."""
        self.outputs_dir = Path(outputs_dir)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

    def _get_job_dir(self, job_id: str) -> Path:
        """Get the output directory for a job."""
        return self.outputs_dir / job_id

    def create_manifest(
        self,
        job_id: str,
        intent: str,
        inventory: Dict,
        steps: Optional[List[Dict]] = None,
    ) -> Dict:
        """Create a new job manifest."""
        job_dir = self._get_job_dir(job_id)
        job_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "job_id": job_id,
            "intent": intent,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "inventory": {
                "total_files": inventory.get("total_files", 0),
                "type_counts": inventory.get("type_counts", {}),
            },
            "steps": steps or [],
            "outputs": {
                "images": [],
                "docs": [],
                "misc": [],
            },
            "errors": [],
        }

        self.save_manifest(job_id, manifest)
        logger.info(f"Created manifest for job {job_id}")
        return manifest

    def save_manifest(self, job_id: str, manifest: Dict):
        """Save manifest to disk."""
        job_dir = self._get_job_dir(job_id)
        manifest_file = job_dir / "manifest.json"

        # Update timestamp
        manifest["updated_at"] = datetime.utcnow().isoformat() + "Z"

        try:
            with open(manifest_file, "w") as f:
                json.dump(manifest, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving manifest for job {job_id}: {e}")
            raise

    def load_manifest(self, job_id: str) -> Optional[Dict]:
        """Load manifest from disk."""
        job_dir = self._get_job_dir(job_id)
        manifest_file = job_dir / "manifest.json"

        if not manifest_file.exists():
            return None

        try:
            with open(manifest_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading manifest for job {job_id}: {e}")
            return None

    def update_status(self, job_id: str, status: str):
        """Update job status."""
        manifest = self.load_manifest(job_id)
        if not manifest:
            raise ValueError(f"Job {job_id} not found")

        manifest["status"] = status
        self.save_manifest(job_id, manifest)

    def add_step(
        self,
        job_id: str,
        step_name: str,
        step_type: str,
        inputs: List[str],
        status: str = "pending",
    ) -> Dict:
        """Add a step to the job manifest."""
        manifest = self.load_manifest(job_id)
        if not manifest:
            raise ValueError(f"Job {job_id} not found")

        step = {
            "name": step_name,
            "type": step_type,
            "status": status,
            "inputs": inputs,
            "outputs": [],
            "started_at": None,
            "completed_at": None,
            "error": None,
        }

        manifest["steps"].append(step)
        self.save_manifest(job_id, manifest)
        return step

    def update_step(
        self,
        job_id: str,
        step_index: int,
        status: Optional[str] = None,
        outputs: Optional[List[str]] = None,
        error: Optional[str] = None,
    ):
        """Update a step in the manifest."""
        manifest = self.load_manifest(job_id)
        if not manifest:
            raise ValueError(f"Job {job_id} not found")

        if step_index >= len(manifest["steps"]):
            raise ValueError(f"Step index {step_index} out of range")

        step = manifest["steps"][step_index]

        if status:
            step["status"] = status
            if status == "running" and not step.get("started_at"):
                step["started_at"] = datetime.utcnow().isoformat() + "Z"
            elif status in ["completed", "failed"]:
                step["completed_at"] = datetime.utcnow().isoformat() + "Z"

        if outputs:
            step["outputs"] = outputs

        if error:
            step["error"] = error
            manifest["errors"].append(error)

        self.save_manifest(job_id, manifest)

    def add_output(self, job_id: str, output_type: str, output_path: str):
        """Add an output file to the manifest."""
        manifest = self.load_manifest(job_id)
        if not manifest:
            raise ValueError(f"Job {job_id} not found")

        if output_type not in manifest["outputs"]:
            manifest["outputs"][output_type] = []

        if output_path not in manifest["outputs"][output_type]:
            manifest["outputs"][output_type].append(output_path)
            self.save_manifest(job_id, manifest)

