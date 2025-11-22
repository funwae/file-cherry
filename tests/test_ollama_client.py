"""
Tests for Ollama client functionality.
"""

import json
from unittest.mock import Mock, patch

import pytest

from src.services.ollama_client import OllamaClient


@pytest.fixture
def ollama_client():
    """Create an OllamaClient instance."""
    return OllamaClient(base_url="http://127.0.0.1:11434")


def test_ollama_client_init(ollama_client):
    """Test OllamaClient initialization."""
    assert ollama_client.base_url == "http://127.0.0.1:11434"
    assert ollama_client.timeout == 300.0


@patch("src.services.ollama_client.httpx.Client")
def test_list_models(mock_client_class, ollama_client):
    """Test listing models."""
    mock_response = Mock()
    mock_response.json.return_value = {"models": [{"name": "phi3:mini"}]}
    mock_response.raise_for_status = Mock()

    mock_client = Mock()
    mock_client.request.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client

    models = ollama_client.list_models()
    assert len(models) == 1
    assert models[0]["name"] == "phi3:mini"


@patch("src.services.ollama_client.httpx.Client")
def test_chat(mock_client_class, ollama_client):
    """Test chat method."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "message": {"content": "Hello, how can I help?"},
        "done": True,
    }
    mock_response.raise_for_status = Mock()

    mock_client = Mock()
    mock_client.request.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client

    messages = [{"role": "user", "content": "Hello"}]
    response = ollama_client.chat("phi3:mini", messages)

    assert response["message"]["content"] == "Hello, how can I help?"
    assert response["done"] is True

    # Verify request was made correctly
    mock_client.request.assert_called_once()
    call_args = mock_client.request.call_args
    assert call_args[0][0] == "POST"
    assert "/api/chat" in call_args[0][1]


@patch("src.services.ollama_client.httpx.Client")
def test_plan(mock_client_class, ollama_client):
    """Test plan method."""
    plan_json = {
        "plan": {
            "summary": "Test plan",
            "steps": [
                {"tool": "IMAGE_PIPELINE", "params": {"input_paths": ["test.jpg"]}}
            ],
        }
    }

    mock_response = Mock()
    mock_response.json.return_value = {
        "message": {"content": json.dumps(plan_json)},
        "done": True,
    }
    mock_response.raise_for_status = Mock()

    mock_client = Mock()
    mock_client.request.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client

    tool_schema = {"tools": []}
    result = ollama_client.plan(
        model="phi3:mini",
        system_prompt="You are a planner",
        user_prompt="Process images",
        tool_schema=tool_schema,
    )

    assert "plan" in result
    assert result["plan"]["summary"] == "Test plan"
    assert len(result["plan"]["steps"]) == 1


def test_parse_json_response_simple(ollama_client):
    """Test parsing simple JSON response."""
    json_str = '{"plan": {"summary": "test"}}'
    result = ollama_client._parse_json_response(json_str)
    assert result["plan"]["summary"] == "test"


def test_parse_json_response_with_markdown(ollama_client):
    """Test parsing JSON from markdown code block."""
    json_str = '```json\n{"plan": {"summary": "test"}}\n```'
    result = ollama_client._parse_json_response(json_str)
    assert result["plan"]["summary"] == "test"


def test_parse_json_response_invalid(ollama_client):
    """Test parsing invalid JSON raises error."""
    with pytest.raises(ValueError):
        ollama_client._parse_json_response("not json")


@patch("src.services.ollama_client.httpx.Client")
def test_health_check_success(mock_client_class, ollama_client):
    """Test health check when Ollama is reachable."""
    mock_response = Mock()
    mock_response.json.return_value = {"models": []}
    mock_response.raise_for_status = Mock()

    mock_client = Mock()
    mock_client.request.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client

    assert ollama_client.health_check() is True


@patch("src.services.ollama_client.httpx.Client")
def test_health_check_failure(mock_client_class, ollama_client):
    """Test health check when Ollama is unreachable."""
    mock_client_class.return_value.__enter__.side_effect = Exception("Connection error")

    assert ollama_client.health_check() is False

