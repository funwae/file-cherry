"""
Planner module.

Loads planner prompts, formats them with inventory and user intent,
calls Ollama, and parses/validates the resulting plan.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from ..services.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class Planner:
    """Handles planning via Ollama LLM."""

    def __init__(
        self,
        ollama_client: OllamaClient,
        prompt_template_path: Optional[Path] = None,
        default_model: str = "phi3:mini",
    ):
        """Initialize planner."""
        self.ollama_client = ollama_client
        self.default_model = default_model

        # Load prompt template
        if prompt_template_path is None:
            # Default to config/llm/planner_prompt.md
            config_dir = Path(__file__).parent.parent.parent / "config" / "llm"
            prompt_template_path = config_dir / "planner_prompt.md"

        self.prompt_template_path = Path(prompt_template_path)
        self.system_prompt = self._load_system_prompt()

        logger.info(f"Planner initialized with model: {default_model}")

    def _load_system_prompt(self) -> str:
        """Load system prompt from template file."""
        if not self.prompt_template_path.exists():
            logger.warning(
                f"Prompt template not found at {self.prompt_template_path}, using default"
            )
            return self._default_system_prompt()

        try:
            with open(self.prompt_template_path, "r") as f:
                content = f.read()
                # Extract system prompt (everything before examples)
                lines = content.split("\n")
                system_lines = []
                for line in lines:
                    if line.startswith("## Examples"):
                        break
                    system_lines.append(line)
                return "\n".join(system_lines).strip()
        except Exception as e:
            logger.error(f"Error loading prompt template: {e}")
            return self._default_system_prompt()

    def _default_system_prompt(self) -> str:
        """Default system prompt if template not found."""
        return """You are the planning brain of FileCherry, an offline AI appliance.

When a user drops files into an "inputs" folder and describes what they want, you must:
1. Analyze the available files (from the inventory provided)
2. Understand the user's intent
3. Create a structured plan using the available tools
4. Return ONLY valid JSON describing the plan

You must respond with ONLY valid JSON in this format:
{
  "plan": {
    "summary": "Brief description of what will be done",
    "steps": [
      {
        "tool": "TOOL_NAME",
        "params": {}
      }
    ]
  }
}"""

    def format_user_prompt(self, intent: str, inventory: Dict) -> str:
        """Format user prompt with intent and inventory."""
        # Summarize inventory
        total_files = inventory.get("total_files", 0)
        type_counts = inventory.get("type_counts", {})
        items = inventory.get("items", [])

        inventory_summary = f"Found {total_files} files:\n"
        for file_type, count in type_counts.items():
            inventory_summary += f"- {count} {file_type}(s)\n"

        # List file paths by type
        inventory_summary += "\nFile paths:\n"
        for item in items[:20]:  # Limit to first 20 for prompt size
            inventory_summary += f"- {item.get('path')} ({item.get('type')})\n"

        if len(items) > 20:
            inventory_summary += f"... and {len(items) - 20} more files\n"

        user_prompt = f"""User intent: {intent}

{inventory_summary}

Create a plan to accomplish the user's request using the available tools."""

        return user_prompt

    def plan(
        self,
        intent: str,
        inventory: Dict,
        tool_schema: Dict,
        model: Optional[str] = None,
    ) -> Dict:
        """
        Create a plan from user intent and inventory.

        Args:
            intent: User's natural language request
            inventory: File inventory from scanner
            tool_schema: Schema of available tools
            model: Ollama model to use (defaults to self.default_model)

        Returns:
            Parsed plan dict with "summary" and "steps"
        """
        model = model or self.default_model

        # Format prompts
        user_prompt = self.format_user_prompt(intent, inventory)

        logger.info(f"Creating plan with model {model} for intent: {intent[:50]}...")

        try:
            plan_data = self.ollama_client.plan(
                model=model,
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                tool_schema=tool_schema,
            )

            # Validate plan structure
            validated_plan = self._validate_plan(plan_data)

            logger.info(f"Plan created: {validated_plan.get('plan', {}).get('summary', 'N/A')}")
            return validated_plan

        except Exception as e:
            logger.error(f"Error creating plan: {e}")
            raise

    def _validate_plan(self, plan_data: Dict) -> Dict:
        """Validate and normalize plan structure."""
        if "plan" not in plan_data:
            raise ValueError("Plan response missing 'plan' key")

        plan = plan_data["plan"]

        # Ensure required fields
        if "summary" not in plan:
            plan["summary"] = "No summary provided"

        if "steps" not in plan:
            plan["steps"] = []

        # Validate steps
        validated_steps = []
        for step in plan["steps"]:
            if "tool" not in step:
                logger.warning("Step missing 'tool' field, skipping")
                continue

            if "params" not in step:
                step["params"] = {}

            validated_steps.append(step)

        plan["steps"] = validated_steps

        return plan_data

