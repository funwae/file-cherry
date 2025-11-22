"""
Tests for ComfyUI client functionality.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.services.comfy_client import ComfyUIClient


@pytest.fixture
def comfy_client():
    """Create a ComfyUIClient instance."""
    return ComfyUIClient(base_url="http://127.0.0.1:8188")


def test_comfy_client_init(comfy_client):
    """Test ComfyUIClient initialization."""
    assert comfy_client.base_url == "http://127.0.0.1:8188"
    assert comfy_client.timeout == 600.0


@patch("src.services.comfy_client.httpx.Client")
def test_health_check_success(mock_client_class, comfy_client):
    """Test health check when ComfyUI is reachable."""
    mock_response = Mock()
    mock_response.raise_for_status = Mock()

    mock_client = Mock()
    mock_client.request.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client

    assert comfy_client.health_check() is True


@patch("src.services.comfy_client.httpx.Client")
def test_health_check_failure(mock_client_class, comfy_client):
    """Test health check when ComfyUI is unreachable."""
    mock_client_class.return_value.__enter__.side_effect = Exception("Connection error")

    assert comfy_client.health_check() is False


@patch("src.services.comfy_client.httpx.Client")
def test_upload_image(mock_client_class, comfy_client):
    """Test uploading an image."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(b"fake image data")
        tmp_path = Path(tmp.name)

    try:
        mock_response = Mock()
        mock_response.json.return_value = {"name": "uploaded_image.jpg"}
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client

        filename = comfy_client.upload_image(tmp_path)

        assert filename == "uploaded_image.jpg"
        mock_client.request.assert_called_once()
    finally:
        tmp_path.unlink()


@patch("src.services.comfy_client.httpx.Client")
def test_queue_prompt(mock_client_class, comfy_client):
    """Test queueing a prompt."""
    mock_response = Mock()
    mock_response.json.return_value = {"prompt_id": "test-prompt-123"}
    mock_response.raise_for_status = Mock()

    mock_client = Mock()
    mock_client.request.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client

    workflow = {"1": {"class_type": "TestNode"}}
    prompt_id = comfy_client.queue_prompt(workflow)

    assert prompt_id == "test-prompt-123"


@patch("src.services.comfy_client.httpx.Client")
def test_get_history(mock_client_class, comfy_client):
    """Test getting history."""
    mock_response = Mock()
    mock_response.json.return_value = {"test-prompt-123": [{"status": "success"}]}
    mock_response.raise_for_status = Mock()

    mock_client = Mock()
    mock_client.request.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client

    history = comfy_client.get_history("test-prompt-123")

    assert len(history) > 0
    assert history[0]["status"] == "success"


@patch("src.services.comfy_client.httpx.Client")
def test_download_image(mock_client_class, comfy_client):
    """Test downloading an image."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "output.jpg"

        mock_response = Mock()
        mock_response.content = b"fake image data"
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client

        result_path = comfy_client.download_image("test_image.jpg", output_path)

        assert result_path.exists()
        assert result_path.read_bytes() == b"fake image data"


@patch("src.services.comfy_client.ComfyUIClient.get_history")
def test_wait_for_completion_success(mock_get_history, comfy_client):
    """Test waiting for completion (success case)."""
    mock_get_history.return_value = [{"status": {"status_str": "success"}}]

    result = comfy_client.wait_for_completion("test-prompt-123", max_wait=1.0)

    assert result["status"]["status_str"] == "success"


@patch("src.services.comfy_client.ComfyUIClient.get_history")
def test_wait_for_completion_timeout(mock_get_history, comfy_client):
    """Test waiting for completion (timeout case)."""
    mock_get_history.return_value = []

    with pytest.raises(TimeoutError):
        comfy_client.wait_for_completion("test-prompt-123", max_wait=0.1, poll_interval=0.05)

