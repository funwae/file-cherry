"""
Pipeline loader and schema management.

Loads pipeline schemas and ComfyUI workflow JSON files.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


class PipelineSchema:
    """Represents a pipeline schema with inputs, params, and outputs."""

    def __init__(self, schema_data: Dict):
        """Initialize from schema dict."""
        self.name = schema_data.get("name", "unknown")
        self.graph_file = schema_data.get("graph_file")
        self.inputs = schema_data.get("inputs", [])
        self.params = schema_data.get("params", [])
        self.outputs = schema_data.get("outputs", [])
        self.semantic_controls = schema_data.get("semantic_controls", {})

    def get_param_default(self, param_name: str):
        """Get default value for a parameter."""
        for param in self.params:
            if param.get("name") == param_name:
                return param.get("default")
        return None

    def get_param_type(self, param_name: str) -> str:
        """Get type for a parameter."""
        for param in self.params:
            if param.get("name") == param_name:
                return param.get("type", "string")
        return "string"


class PipelineLoader:
    """Loads and manages pipeline schemas and workflows."""

    def __init__(self, pipelines_dir: Path):
        """Initialize pipeline loader."""
        self.pipelines_dir = Path(pipelines_dir)
        self.pipelines_dir.mkdir(parents=True, exist_ok=True)
        self.schemas: Dict[str, PipelineSchema] = {}
        self.workflows: Dict[str, Dict] = {}

        logger.info(f"PipelineLoader initialized - pipelines_dir: {self.pipelines_dir}")

    def load_schema(self, schema_name: str) -> Optional[PipelineSchema]:
        """
        Load a pipeline schema by name.

        Args:
            schema_name: Name of the schema (without .yaml extension)

        Returns:
            PipelineSchema or None if not found
        """
        if schema_name in self.schemas:
            return self.schemas[schema_name]

        schema_file = self.pipelines_dir / f"{schema_name}.yaml"
        if not schema_file.exists():
            logger.warning(f"Schema file not found: {schema_file}")
            return None

        try:
            with open(schema_file, "r") as f:
                schema_data = yaml.safe_load(f)

            schema = PipelineSchema(schema_data)
            self.schemas[schema_name] = schema
            logger.info(f"Loaded schema: {schema_name}")
            return schema
        except Exception as e:
            logger.error(f"Error loading schema {schema_name}: {e}")
            return None

    def load_workflow(self, graph_file: str) -> Optional[Dict]:
        """
        Load a ComfyUI workflow JSON file.

        Args:
            graph_file: Filename of the workflow JSON

        Returns:
            Workflow dict or None if not found
        """
        if graph_file in self.workflows:
            return self.workflows[graph_file]

        workflow_file = self.pipelines_dir / graph_file
        if not workflow_file.exists():
            logger.warning(f"Workflow file not found: {workflow_file}")
            return None

        try:
            with open(workflow_file, "r") as f:
                workflow = json.load(f)

            self.workflows[graph_file] = workflow
            logger.info(f"Loaded workflow: {graph_file}")
            return workflow
        except Exception as e:
            logger.error(f"Error loading workflow {graph_file}: {e}")
            return None

    def apply_semantic_controls(
        self, workflow: Dict, schema: PipelineSchema, style_hints: List[str]
    ) -> Dict:
        """
        Apply semantic controls to workflow based on style hints.

        Args:
            workflow: ComfyUI workflow dict
            schema: Pipeline schema
            style_hints: List of style hints (e.g., ["premium", "less_saturated"])

        Returns:
            Modified workflow
        """
        workflow = json.loads(json.dumps(workflow))  # Deep copy

        # Apply semantic controls
        for hint in style_hints:
            if hint in schema.semantic_controls:
                controls = schema.semantic_controls[hint]
                for param_name, value in controls.items():
                    # Find and update the parameter in the workflow
                    # This is simplified - real implementation would need to
                    # map param names to node IDs
                    logger.info(f"Applying semantic control: {param_name} = {value}")

        return workflow

    def prepare_workflow(
        self,
        schema_name: str,
        input_paths: List[str],
        params: Optional[Dict] = None,
        style_hints: Optional[List[str]] = None,
    ) -> Optional[Dict]:
        """
        Prepare a workflow for execution.

        Args:
            schema_name: Name of the pipeline schema
            input_paths: List of input file paths
            params: Optional parameter overrides
            style_hints: Optional style hints for semantic controls

        Returns:
            Prepared workflow dict or None
        """
        schema = self.load_schema(schema_name)
        if not schema:
            return None

        workflow = self.load_workflow(schema.graph_file)
        if not workflow:
            return None

        # Apply semantic controls if provided
        if style_hints:
            workflow = self.apply_semantic_controls(workflow, schema, style_hints)

        # Apply parameter overrides
        if params:
            # This would need to map params to workflow nodes
            # Simplified for now
            logger.info(f"Applying parameter overrides: {list(params.keys())}")

        return workflow

    def list_pipelines(self) -> List[str]:
        """List available pipeline schemas."""
        schemas = []
        for yaml_file in self.pipelines_dir.glob("*.yaml"):
            schemas.append(yaml_file.stem)
        return schemas

