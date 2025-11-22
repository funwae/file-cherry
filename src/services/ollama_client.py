"""
Ollama HTTP client.

Provides interface to Ollama API for chat and planning operations.
"""

import json
import logging
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama API."""

    def __init__(self, base_url: str = "http://127.0.0.1:11434", timeout: float = 300.0):
        """Initialize Ollama client."""
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        logger.info(f"OllamaClient initialized - base_url: {self.base_url}")

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make HTTP request to Ollama API."""
        url = f"{self.base_url}{endpoint}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Ollama API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Ollama: {e}")
            raise

    def list_models(self) -> List[Dict]:
        """List available models."""
        try:
            response = self._request("GET", "/api/tags")
            return response.get("models", [])
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []

    def chat(
        self,
        model: str,
        messages: List[Dict],
        stream: bool = False,
        format: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        Send chat request to Ollama.

        Args:
            model: Model name (e.g., "phi3:mini")
            messages: List of message dicts with "role" and "content"
            stream: Whether to stream response
            format: Optional JSON schema for structured output
            **kwargs: Additional parameters (temperature, etc.)

        Returns:
            Response dict with "message" and "done" fields
        """
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }

        if format:
            payload["format"] = format

        payload.update(kwargs)

        try:
            response = self._request("POST", "/api/chat", json=payload)
            return response
        except Exception as e:
            logger.error(f"Error in chat request: {e}")
            raise

    def plan(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        tool_schema: Dict,
        temperature: float = 0.3,
    ) -> Dict:
        """
        Request a structured plan from Ollama.

        Args:
            model: Model name
            system_prompt: System prompt describing the planning task
            user_prompt: User's intent and file inventory
            tool_schema: Schema of available tools
            temperature: Sampling temperature (lower for more deterministic)

        Returns:
            Parsed plan dict with "summary" and "steps"
        """
        # Format the prompt with tool schema
        full_prompt = f"""{user_prompt}

Available tools:
{json.dumps(tool_schema, indent=2)}

You must respond with ONLY valid JSON in this exact format:
{{
  "plan": {{
    "summary": "Brief description of the plan",
    "steps": [
      {{
        "tool": "TOOL_NAME",
        "params": {{}}
      }}
    ]
  }}
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt},
        ]

        # Request JSON format
        json_schema = {
            "type": "object",
            "properties": {
                "plan": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                        "steps": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "tool": {"type": "string"},
                                    "params": {"type": "object"},
                                },
                                "required": ["tool", "params"],
                            },
                        },
                    },
                    "required": ["summary", "steps"],
                }
            },
            "required": ["plan"],
        }

        try:
            response = self.chat(
                model=model,
                messages=messages,
                format=json.dumps(json_schema),
                temperature=temperature,
            )

            # Extract and parse JSON from response
            content = response.get("message", {}).get("content", "")
            plan_data = self._parse_json_response(content)

            return plan_data
        except Exception as e:
            logger.error(f"Error in plan request: {e}")
            raise

    def _parse_json_response(self, content: str) -> Dict:
        """Parse JSON from LLM response, handling markdown code blocks."""
        content = content.strip()

        # Remove markdown code blocks if present
        if content.startswith("```"):
            lines = content.split("\n")
            # Remove first line (```json or ```)
            lines = lines[1:]
            # Remove last line (```)
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines)

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Content: {content[:500]}")
            raise ValueError(f"Invalid JSON response from Ollama: {e}")

    async def chat_async(
        self,
        model: str,
        messages: List[Dict],
        stream: bool = False,
        format: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        Send async chat request to Ollama.

        Args:
            model: Model name (e.g., "phi3:mini")
            messages: List of message dicts with "role" and "content"
            stream: Whether to stream response
            format: Optional JSON schema for structured output
            **kwargs: Additional parameters (temperature, etc.)

        Returns:
            Response dict with "message" and "done" fields
        """
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }

        if format:
            payload["format"] = format

        payload.update(kwargs)

        url = f"{self.base_url}/api/chat"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Ollama API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Ollama: {e}")
            raise

    def health_check(self) -> bool:
        """Check if Ollama service is reachable."""
        try:
            self.list_models()
            return True
        except Exception:
            return False
