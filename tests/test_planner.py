"""
Tests for planner functionality.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.orchestrator.planner import Planner
from src.services.ollama_client import OllamaClient


@pytest.fixture
def mock_ollama_client():
    """Create a mock OllamaClient."""
    client = Mock(spec=OllamaClient)
    return client


@pytest.fixture
def planner(mock_ollama_client):
    """Create a Planner instance with mock client."""
    return Planner(ollama_client=mock_ollama_client, default_model="phi3:mini")


def test_planner_init(planner, mock_ollama_client):
    """Test Planner initialization."""
    assert planner.ollama_client == mock_ollama_client
    assert planner.default_model == "phi3:mini"
    assert planner.system_prompt is not None
    assert len(planner.system_prompt) > 0


def test_load_system_prompt_from_file():
    """Test loading system prompt from file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        prompt_file = Path(tmpdir) / "planner_prompt.md"
        prompt_file.write_text("# System Prompt\n\nThis is a test prompt.")

        client = Mock(spec=OllamaClient)
        planner = Planner(client, prompt_template_path=prompt_file)

        assert "System Prompt" in planner.system_prompt
        assert "This is a test prompt" in planner.system_prompt


def test_format_user_prompt(planner):
    """Test formatting user prompt with intent and inventory."""
    intent = "Process all images"
    inventory = {
        "total_files": 3,
        "type_counts": {"image": 2, "document": 1},
        "items": [
            {"path": "inputs/img1.jpg", "type": "image"},
            {"path": "inputs/img2.jpg", "type": "image"},
            {"path": "inputs/doc1.pdf", "type": "document"},
        ],
    }

    prompt = planner.format_user_prompt(intent, inventory)

    assert intent in prompt
    assert "3 files" in prompt
    assert "2 image(s)" in prompt
    assert "1 document(s)" in prompt
    assert "img1.jpg" in prompt
    assert "doc1.pdf" in prompt


def test_plan_success(planner, mock_ollama_client):
    """Test successful plan creation."""
    plan_data = {
        "plan": {
            "summary": "Process images and documents",
            "steps": [
                {
                    "tool": "IMAGE_PIPELINE",
                    "params": {"input_paths": ["img1.jpg"], "purpose": "cleanup"},
                },
                {
                    "tool": "DOC_ANALYSIS",
                    "params": {"input_paths": ["doc1.pdf"], "query": "summarize"},
                },
            ],
        }
    }

    mock_ollama_client.plan.return_value = plan_data

    intent = "Process files"
    inventory = {"total_files": 2, "type_counts": {}, "items": []}
    tool_schema = {"tools": []}

    result = planner.plan(intent, inventory, tool_schema)

    assert result["plan"]["summary"] == "Process images and documents"
    assert len(result["plan"]["steps"]) == 2
    mock_ollama_client.plan.assert_called_once()


def test_plan_validation_missing_summary(planner, mock_ollama_client):
    """Test plan validation adds default summary if missing."""
    plan_data = {
        "plan": {
            "steps": [{"tool": "IMAGE_PIPELINE", "params": {}}],
        }
    }

    mock_ollama_client.plan.return_value = plan_data

    result = planner.plan("test", {"total_files": 0, "type_counts": {}, "items": []}, {})

    assert result["plan"]["summary"] == "No summary provided"
    assert len(result["plan"]["steps"]) == 1


def test_plan_validation_missing_steps(planner, mock_ollama_client):
    """Test plan validation adds empty steps if missing."""
    plan_data = {"plan": {"summary": "Test plan"}}

    mock_ollama_client.plan.return_value = plan_data

    result = planner.plan("test", {"total_files": 0, "type_counts": {}, "items": []}, {})

    assert result["plan"]["steps"] == []


def test_plan_validation_invalid_step(planner, mock_ollama_client):
    """Test plan validation skips invalid steps."""
    plan_data = {
        "plan": {
            "summary": "Test",
            "steps": [
                {"tool": "IMAGE_PIPELINE", "params": {}},
                {"params": {}},  # Missing tool
                {"tool": "DOC_ANALYSIS"},  # Missing params
            ],
        }
    }

    mock_ollama_client.plan.return_value = plan_data

    result = planner.plan("test", {"total_files": 0, "type_counts": {}, "items": []}, {})

    # Should have 2 valid steps (first and third)
    assert len(result["plan"]["steps"]) == 2


def test_plan_error_handling(planner, mock_ollama_client):
    """Test plan error handling."""
    mock_ollama_client.plan.side_effect = Exception("Ollama error")

    with pytest.raises(Exception):
        planner.plan("test", {"total_files": 0, "type_counts": {}, "items": []}, {})

