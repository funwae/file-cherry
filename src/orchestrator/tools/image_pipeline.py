"""
IMAGE_PIPELINE tool implementation.

Processes images through ComfyUI pipelines.
"""

import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

from ...services.comfy_client import ComfyUIClient
from ...services.pipeline_loader import PipelineLoader

logger = logging.getLogger(__name__)


class ImagePipelineTool:
    """Tool for processing images via ComfyUI."""

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        comfy_client: Optional[ComfyUIClient] = None,
        pipeline_loader: Optional[PipelineLoader] = None,
    ):
        """Initialize image pipeline tool."""
        # Get directories from environment or use defaults
        if data_dir is None:
            data_dir = Path(os.getenv("FILECHERRY_DATA_DIR", "/data"))

        self.data_dir = Path(data_dir)
        self.inputs_dir = self.data_dir / "inputs"
        self.outputs_dir = self.data_dir / "outputs"

        # Initialize services
        self.comfy_client = comfy_client or ComfyUIClient()
        self.pipeline_loader = pipeline_loader or PipelineLoader(
            self.data_dir / "config" / "comfy" / "pipelines"
        )

        logger.info("ImagePipelineTool initialized")

    def _select_pipeline(self, purpose: str) -> str:
        """
        Select appropriate pipeline based on purpose.

        Args:
            purpose: Description of what to do

        Returns:
            Pipeline schema name
        """
        purpose_lower = purpose.lower()

        # Simple heuristic-based selection
        if any(word in purpose_lower for word in ["clean", "cleanup", "enhance", "polish"]):
            return "photo_cleanup_v1"
        elif any(word in purpose_lower for word in ["variation", "variant", "generate"]):
            # Would use creative_variation pipeline if available
            return "photo_cleanup_v1"  # Fallback
        else:
            # Default to cleanup
            return "photo_cleanup_v1"

    def _extract_style_hints(self, style: Optional[str]) -> List[str]:
        """
        Extract style hints from style string.

        Args:
            style: Style description string

        Returns:
            List of style hint keywords
        """
        if not style:
            return []

        style_lower = style.lower()
        hints = []

        # Map common style terms to semantic controls
        style_mappings = {
            "premium": "premium",
            "professional": "professional",
            "bright": "bright",
            "vibrant": "vibrant",
            "muted": "muted",
            "less saturated": "less_saturated",
            "saturated": "vibrant",
        }

        for term, hint in style_mappings.items():
            if term in style_lower:
                hints.append(hint)

        return hints

    def execute(
        self,
        purpose: str,
        input_paths: List[str],
        style: Optional[str] = None,
        job_id: Optional[str] = None,
        manifest_manager=None,
    ) -> Dict:
        """
        Execute image pipeline processing.

        Args:
            purpose: What to do with the images
            input_paths: List of image file paths
            style: Optional style preferences
            job_id: Job ID for tracking
            manifest_manager: Manifest manager for updating job state

        Returns:
            Dict with execution results
        """
        logger.info(f"Executing IMAGE_PIPELINE: {purpose} for {len(input_paths)} images")

        outputs = []
        errors = []

        # Select pipeline
        pipeline_name = self._select_pipeline(purpose)
        logger.info(f"Selected pipeline: {pipeline_name}")

        # Extract style hints
        style_hints = self._extract_style_hints(style)

        # Setup output directory
        if job_id:
            output_dir = self.outputs_dir / job_id / "images"
        else:
            output_dir = self.outputs_dir / "temp" / "images"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Process each image
        for input_path in input_paths:
            try:
                # Resolve full path
                if Path(input_path).is_absolute():
                    full_input_path = Path(input_path)
                else:
                    full_input_path = self.inputs_dir / input_path

                if not full_input_path.exists():
                    errors.append(f"Image not found: {input_path}")
                    continue

                # Upload image to ComfyUI
                logger.info(f"Uploading image: {full_input_path}")
                uploaded_filename = self.comfy_client.upload_image(full_input_path)

                # Prepare workflow
                workflow = self.pipeline_loader.prepare_workflow(
                    schema_name=pipeline_name,
                    input_paths=[str(full_input_path)],
                    style_hints=style_hints,
                )

                if not workflow:
                    errors.append(f"Failed to prepare workflow for {input_path}")
                    continue

                # Replace image input placeholder
                workflow = self._inject_image_input(workflow, uploaded_filename)

                # Queue workflow
                prompt_id = self.comfy_client.queue_prompt(workflow)

                # Wait for completion
                logger.info(f"Waiting for prompt {prompt_id} to complete...")
                result = self.comfy_client.wait_for_completion(prompt_id)

                # Check for errors
                if result.get("status", {}).get("status_str") == "error":
                    error_msg = result.get("status", {}).get("messages", ["Unknown error"])
                    errors.append(f"{input_path}: {error_msg}")
                    continue

                # Download output images
                output_filenames = self.comfy_client.get_output_images(prompt_id)

                for idx, filename in enumerate(output_filenames):
                    output_filename = f"{full_input_path.stem}_processed_{idx}{full_input_path.suffix}"
                    output_path = output_dir / output_filename

                    self.comfy_client.download_image(filename, output_path)

                    # Store relative path
                    rel_path = output_path.relative_to(self.data_dir)
                    outputs.append(str(rel_path))
                    logger.info(f"Saved processed image: {rel_path}")

            except Exception as e:
                error_msg = f"Error processing {input_path}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue

        # Update manifest if provided
        if manifest_manager and job_id:
            step_index = len(manifest_manager.load_manifest(job_id)["steps"])
            manifest_manager.update_step(
                job_id=job_id,
                step_index=step_index,
                status="completed" if not errors else "partial",
                outputs=outputs,
                error="; ".join(errors) if errors else None,
            )

        return {
            "tool": "IMAGE_PIPELINE",
            "status": "completed" if not errors else "partial",
            "input_count": len(input_paths),
            "outputs": outputs,
            "errors": errors,
        }

    def _inject_image_input(self, workflow: Dict, image_filename: str) -> Dict:
        """
        Inject image input into workflow.

        Args:
            workflow: ComfyUI workflow dict
            image_filename: Uploaded image filename

        Returns:
            Modified workflow
        """
        # This is a simplified implementation
        # Real ComfyUI workflows have specific node structures
        # For now, we'll try to find and replace image input nodes

        workflow = self._deep_copy_dict(workflow)

        # Look for LoadImage nodes and update them
        for node_id, node_data in workflow.items():
            if isinstance(node_data, dict) and node_data.get("class_type") == "LoadImage":
                if "inputs" in node_data:
                    node_data["inputs"]["image"] = image_filename

        return workflow

    def _deep_copy_dict(self, d: Dict) -> Dict:
        """Deep copy a dictionary."""
        import json

        return json.loads(json.dumps(d))
