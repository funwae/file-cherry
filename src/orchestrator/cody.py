"""
Cody chat functionality.

Handles Cody's persona and chat interactions.
"""

import os
import logging
from pathlib import Path
from typing import List, Optional

from ..services.ollama_client import OllamaClient
from .models.cody_chat import CodyMessage

logger = logging.getLogger(__name__)

# Cache for system prompt
_cody_system_prompt: str | None = None

CODY_MODEL = os.getenv("CODY_MODEL", "phi3:mini")
CODY_SYSTEM_PROMPT_PATH = os.getenv(
    "CODY_SYSTEM_PROMPT_PATH",
    "/opt/filecherry/config/llm/cody_system_prompt.md",
)


def load_cody_system_prompt() -> str:
    """Load Cody's system prompt from file."""
    global _cody_system_prompt

    if _cody_system_prompt is not None:
        return _cody_system_prompt

    # Try multiple paths
    paths = [
        Path(CODY_SYSTEM_PROMPT_PATH),
        Path(__file__).parent.parent.parent / "config" / "llm" / "cody_system_prompt.md",
        Path(os.getenv("FILECHERRY_DATA_DIR", "/data")) / "config" / "llm" / "cody_system_prompt.md",
    ]

    for path in paths:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    _cody_system_prompt = f.read()
                    logger.info(f"Loaded Cody system prompt from {path}")
                    return _cody_system_prompt
            except Exception as e:
                logger.warning(f"Error loading Cody prompt from {path}: {e}")
                continue

    # Fallback prompt if file not found
    logger.warning("Cody system prompt file not found, using fallback")
    _cody_system_prompt = """You are Cody the Cherry Picker, the mascot of FileCherry.
FileCherry is a bootable AI appliance on a USB stick.
Be plainspoken, helpful, and slightly impatient. Roast messy files, not users."""
    return _cody_system_prompt


async def cody_chat(messages: List[CodyMessage], ollama_client: Optional[OllamaClient] = None) -> str:
    """
    Chat with Cody using Ollama.

    Args:
        messages: List of chat messages
        ollama_client: Optional Ollama client (creates one if not provided)

    Returns:
        Cody's reply as a string
    """
    if ollama_client is None:
        ollama_client = OllamaClient()

    system_prompt = load_cody_system_prompt()

    # Build message list for Ollama
    ollama_messages: List[dict] = [
        {"role": "system", "content": system_prompt}
    ]

    # Add user/assistant messages (skip any system messages from client)
    for msg in messages:
        if msg.role == "system":
            continue  # Ignore extra system messages; Cody persona is fixed
        ollama_messages.append({"role": msg.role, "content": msg.content})

    try:
        # Call Ollama chat API
        response = await ollama_client.chat_async(
            model=CODY_MODEL,
            messages=ollama_messages,
            stream=False,
        )

        # Extract reply from response
        if isinstance(response, dict):
            message = response.get("message", {})
            if isinstance(message, dict):
                reply = message.get("content", "Cody didn't respond.")
            else:
                reply = str(message)
        else:
            reply = str(response)

        return reply

    except Exception as e:
        logger.error(f"Error in Cody chat: {e}")
        return f"Cody dropped a sack on that one. Error: {str(e)}"

