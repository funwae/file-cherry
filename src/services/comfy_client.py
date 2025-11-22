"""
ComfyUI HTTP client.

Provides interface to ComfyUI API for workflow execution and image handling.
"""

import json
import logging
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class ComfyUIClient:
    """Client for interacting with ComfyUI API."""

    def __init__(self, base_url: str = "http://127.0.0.1:8188", timeout: float = 600.0):
        """Initialize ComfyUI client."""
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        logger.info(f"ComfyUIClient initialized - base_url: {self.base_url}")

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make HTTP request to ComfyUI API."""
        url = f"{self.base_url}{endpoint}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(method, url, **kwargs)
                response.raise_for_status()
                if response.headers.get("content-type", "").startswith("application/json"):
                    return response.json()
                return {"status": "ok", "data": response.text}
        except httpx.HTTPError as e:
            logger.error(f"ComfyUI API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling ComfyUI: {e}")
            raise

    def health_check(self) -> bool:
        """Check if ComfyUI service is reachable."""
        try:
            self._request("GET", "/")
            return True
        except Exception:
            return False

    def upload_image(self, image_path: Path) -> str:
        """
        Upload image to ComfyUI.

        Args:
            image_path: Path to image file

        Returns:
            Image filename in ComfyUI format
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        try:
            with open(image_path, "rb") as f:
                files = {"image": (image_path.name, f, "image/jpeg")}
                response = self._request("POST", "/upload/image", files=files)

            # ComfyUI returns the filename
            filename = response.get("name", image_path.name)
            logger.info(f"Uploaded image: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error uploading image {image_path}: {e}")
            raise

    def queue_prompt(self, workflow: Dict, client_id: Optional[str] = None) -> str:
        """
        Queue a workflow for execution.

        Args:
            workflow: ComfyUI workflow JSON
            client_id: Optional client ID for tracking

        Returns:
            Prompt ID
        """
        if client_id is None:
            client_id = str(uuid.uuid4())

        payload = {
            "prompt": workflow,
            "client_id": client_id,
        }

        try:
            response = self._request("POST", "/prompt", json=payload)
            prompt_id = response.get("prompt_id")
            if not prompt_id:
                raise ValueError("No prompt_id in response")
            logger.info(f"Queued prompt: {prompt_id}")
            return prompt_id
        except Exception as e:
            logger.error(f"Error queueing prompt: {e}")
            raise

    def get_history(self, prompt_id: Optional[str] = None) -> List[Dict]:
        """
        Get execution history.

        Args:
            prompt_id: Optional specific prompt ID

        Returns:
            List of history entries
        """
        try:
            response = self._request("GET", "/history")
            history = response.get(prompt_id, []) if prompt_id else response
            return history if isinstance(history, list) else [history]
        except Exception as e:
            logger.error(f"Error getting history: {e}")
            return []

    def get_progress(self) -> Dict:
        """
        Get current progress.

        Returns:
            Progress information
        """
        try:
            response = self._request("GET", "/progress")
            return response
        except Exception as e:
            logger.error(f"Error getting progress: {e}")
            return {"status": "unknown"}

    def wait_for_completion(
        self, prompt_id: str, poll_interval: float = 1.0, max_wait: float = 300.0
    ) -> Dict:
        """
        Wait for a prompt to complete.

        Args:
            prompt_id: Prompt ID to wait for
            poll_interval: Seconds between polls
            max_wait: Maximum time to wait

        Returns:
            Final history entry
        """
        start_time = time.time()

        while time.time() - start_time < max_wait:
            history = self.get_history(prompt_id)
            if history:
                entry = history[0]
                status = entry.get("status", {}).get("status_str", "unknown")
                if status in ["success", "error"]:
                    logger.info(f"Prompt {prompt_id} completed with status: {status}")
                    return entry

            time.sleep(poll_interval)

        raise TimeoutError(f"Prompt {prompt_id} did not complete within {max_wait}s")

    def download_image(self, filename: str, output_path: Path) -> Path:
        """
        Download generated image from ComfyUI.

        Args:
            filename: Image filename from ComfyUI
            output_path: Where to save the image

        Returns:
            Path to saved image
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # ComfyUI serves images at /view?filename=...
            url = f"{self.base_url}/view"
            params = {"filename": filename}

            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, params=params)
                response.raise_for_status()

                with open(output_path, "wb") as f:
                    f.write(response.content)

            logger.info(f"Downloaded image to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error downloading image {filename}: {e}")
            raise

    def get_output_images(self, prompt_id: str) -> List[str]:
        """
        Get list of output image filenames from a completed prompt.

        Args:
            prompt_id: Prompt ID

        Returns:
            List of image filenames
        """
        history = self.get_history(prompt_id)
        if not history:
            return []

        images = []
        for entry in history:
            outputs = entry.get("outputs", {})
            for node_id, node_output in outputs.items():
                if "images" in node_output:
                    for img in node_output["images"]:
                        filename = img.get("filename")
                        if filename:
                            images.append(filename)

        return images
