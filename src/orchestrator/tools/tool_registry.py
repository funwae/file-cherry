"""
Tool registry and definitions.

Defines available tools and their schemas for the planner.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# Tool schema definitions
TOOL_SCHEMA = {
    "tools": [
        {
            "name": "IMAGE_PIPELINE",
            "description": "Process images through ComfyUI pipelines (cleanup, enhancement, style transfer, etc.)",
            "params": {
                "purpose": {
                    "type": "string",
                    "description": "What to do with the images (e.g., 'dealership-ready car photos', 'product enhancement')",
                    "required": True,
                },
                "style": {
                    "type": "string",
                    "description": "Style preferences (e.g., 'bright, neutral background', 'premium look')",
                    "required": False,
                },
                "input_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of image file paths from inputs/",
                    "required": True,
                },
            },
        },
        {
            "name": "DOC_ANALYSIS",
            "description": "Analyze documents (summarize, search, compile by subject, Q&A)",
            "params": {
                "query": {
                    "type": "string",
                    "description": "What to analyze or find in the documents",
                    "required": True,
                },
                "input_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of document file paths from inputs/",
                    "required": True,
                },
                "output_kind": {
                    "type": "string",
                    "enum": ["summary", "qa", "clustered_report"],
                    "description": "Type of output to generate",
                    "required": False,
                    "default": "summary",
                },
            },
        },
    ]
}


class ToolRegistry:
    """Registry of available tools."""

    def __init__(self):
        """Initialize tool registry."""
        self.tools: Dict[str, callable] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """Register default tool implementations."""
        import os
        from pathlib import Path

        from .image_pipeline import ImagePipelineTool
        from .doc_analysis import DocAnalysisTool
        from ...services.ollama_client import OllamaClient
        from ...services.comfy_client import ComfyUIClient
        from ...services.pipeline_loader import PipelineLoader

        # Initialize clients
        ollama_client = OllamaClient()
        comfy_client = ComfyUIClient()

        # Get data directory
        data_dir = Path(os.getenv("FILECHERRY_DATA_DIR", "/data"))
        runtime_dir = data_dir / "runtime"

        # Initialize pipeline loader
        pipeline_loader = PipelineLoader(data_dir / "config" / "comfy" / "pipelines")

        self.register(
            "IMAGE_PIPELINE",
            ImagePipelineTool(
                data_dir=data_dir,
                comfy_client=comfy_client,
                pipeline_loader=pipeline_loader,
            ),
        )
        self.register(
            "DOC_ANALYSIS",
            DocAnalysisTool(
                data_dir=data_dir,
                runtime_dir=runtime_dir,
                ollama_client=ollama_client,
            ),
        )

    def register(self, tool_name: str, tool_instance):
        """Register a tool instance."""
        self.tools[tool_name] = tool_instance
        logger.info(f"Registered tool: {tool_name}")

    def get_tool(self, tool_name: str):
        """Get a tool instance by name."""
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        return self.tools[tool_name]

    def get_schema(self) -> Dict:
        """Get the tool schema for the planner."""
        return TOOL_SCHEMA

    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self.tools.keys())


# Global registry instance
_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get the global tool registry."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry

