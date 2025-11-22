"""
Job management and execution.

Manages job state machine and coordinates execution of job steps.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Optional

from .manifest import ManifestManager
from .planner import Planner
from .tools.tool_registry import get_registry

logger = logging.getLogger(__name__)


class JobManager:
    """Manages job lifecycle and execution."""

    def __init__(
        self,
        manifest_manager: ManifestManager,
        planner: Optional[Planner] = None,
    ):
        """Initialize job manager."""
        self.manifest_manager = manifest_manager
        self.planner = planner
        self.tool_registry = get_registry()
        self.active_jobs: Dict[str, Dict] = {}

    def _generate_job_id(self) -> str:
        """Generate a unique job ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        random_suffix = str(uuid.uuid4())[:6]
        return f"{timestamp}-{random_suffix}"

    def create_job(self, intent: str, inventory: Dict) -> str:
        """Create a new job from user intent and inventory."""
        job_id = self._generate_job_id()

        # Create manifest
        manifest = self.manifest_manager.create_manifest(
            job_id=job_id,
            intent=intent,
            inventory=inventory,
            steps=[],
        )

        # Store in active jobs
        self.active_jobs[job_id] = {
            "job_id": job_id,
            "status": "pending",
            "intent": intent,
            "manifest": manifest,
        }

        logger.info(f"Created job {job_id} with intent: {intent[:50]}...")
        return job_id

    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job information."""
        if job_id in self.active_jobs:
            return self.active_jobs[job_id]

        # Try loading from manifest
        manifest = self.manifest_manager.load_manifest(job_id)
        if manifest:
            return {
                "job_id": job_id,
                "status": manifest.get("status", "unknown"),
                "intent": manifest.get("intent", ""),
                "manifest": manifest,
            }

        return None

    def start_job(self, job_id: str):
        """Start executing a job."""
        job = self.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if job["status"] != "pending":
            raise ValueError(f"Job {job_id} is not in pending state")

        # Update status
        self.manifest_manager.update_status(job_id, "running")
        self.active_jobs[job_id]["status"] = "running"

        logger.info(f"Started job {job_id}")

        # Execute the job
        self._execute(job_id)

    def _execute(self, job_id: str):
        """Execute a job: plan, then execute steps."""
        manifest = self.manifest_manager.load_manifest(job_id)
        if not manifest:
            raise ValueError(f"Manifest not found for job {job_id}")

        intent = manifest["intent"]
        inventory = manifest.get("inventory", {})

        # Step 1: Create plan using planner
        if self.planner:
            try:
                tool_schema = self.tool_registry.get_schema()
                plan_data = self.planner.plan(intent, inventory, tool_schema)

                plan = plan_data.get("plan", {})
                steps = plan.get("steps", [])

                logger.info(f"Plan created with {len(steps)} steps: {plan.get('summary', 'N/A')}")

                # Store plan in manifest
                manifest["plan"] = plan
                self.manifest_manager.save_manifest(job_id, manifest)

            except Exception as e:
                logger.error(f"Error creating plan for job {job_id}: {e}")
                self.manifest_manager.update_status(job_id, "failed")
                if job_id in self.active_jobs:
                    self.active_jobs[job_id]["status"] = "failed"
                raise

        else:
            logger.warning("No planner available, using mock execution")
            self._mock_execute(job_id)
            return

        # Step 2: Execute each step in the plan
        try:
            for step_idx, step in enumerate(steps):
                tool_name = step.get("tool")
                params = step.get("params", {})

                if not tool_name:
                    logger.warning(f"Step {step_idx} missing tool name, skipping")
                    continue

                # Get tool instance
                try:
                    tool = self.tool_registry.get_tool(tool_name)
                except ValueError as e:
                    logger.error(f"Unknown tool {tool_name}: {e}")
                    self.manifest_manager.add_step(
                        job_id=job_id,
                        step_name=f"step_{step_idx}",
                        step_type=tool_name,
                        inputs=params.get("input_paths", []),
                        status="failed",
                    )
                    continue

                # Add step to manifest
                step_index = len(manifest["steps"])
                self.manifest_manager.add_step(
                    job_id=job_id,
                    step_name=f"step_{step_idx}_{tool_name.lower()}",
                    step_type=tool_name,
                    inputs=params.get("input_paths", []),
                    status="pending",
                )

                # Execute tool
                try:
                    logger.info(f"Executing {tool_name} with params: {list(params.keys())}")
                    result = tool.execute(
                        job_id=job_id,
                        manifest_manager=self.manifest_manager,
                        **params
                    )

                    # Update step status
                    self.manifest_manager.update_step(
                        job_id=job_id,
                        step_index=step_index,
                        status="completed",
                        outputs=result.get("outputs", []),
                    )

                except Exception as e:
                    logger.error(f"Error executing {tool_name}: {e}")
                    self.manifest_manager.update_step(
                        job_id=job_id,
                        step_index=step_index,
                        status="failed",
                        error=str(e),
                    )

            # Mark job as completed
            self.manifest_manager.update_status(job_id, "completed")
            if job_id in self.active_jobs:
                self.active_jobs[job_id]["status"] = "completed"

            logger.info(f"Job {job_id} execution completed")

        except Exception as e:
            logger.error(f"Error executing job {job_id}: {e}")
            self.manifest_manager.update_status(job_id, "failed")
            if job_id in self.active_jobs:
                self.active_jobs[job_id]["status"] = "failed"
            raise

    def _mock_execute(self, job_id: str):
        """Mock job execution fallback."""
        # Add a mock step
        step = self.manifest_manager.add_step(
            job_id=job_id,
            step_name="mock_processing",
            step_type="mock",
            inputs=[],
            status="running",
        )

        # Simulate some work
        import time
        time.sleep(0.1)

        # Mark step as completed
        step_index = len(self.manifest_manager.load_manifest(job_id)["steps"]) - 1
        self.manifest_manager.update_step(
            job_id=job_id,
            step_index=step_index,
            status="completed",
            outputs=["mock_output.txt"],
        )

        # Mark job as completed
        self.manifest_manager.update_status(job_id, "completed")
        if job_id in self.active_jobs:
            self.active_jobs[job_id]["status"] = "completed"

        logger.info(f"Mock execution completed for job {job_id}")

    def cancel_job(self, job_id: str):
        """Cancel a running job."""
        job = self.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if job["status"] not in ["pending", "running"]:
            raise ValueError(f"Cannot cancel job {job_id} in state {job['status']}")

        self.manifest_manager.update_status(job_id, "cancelled")
        if job_id in self.active_jobs:
            self.active_jobs[job_id]["status"] = "cancelled"

        logger.info(f"Cancelled job {job_id}")

