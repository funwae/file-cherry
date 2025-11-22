"""
Tests for image pipeline tool functionality.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.orchestrator.tools.image_pipeline import ImagePipelineTool
from src.services.comfy_client import ComfyUIClient
from src.services.pipeline_loader import PipelineLoader


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        inputs_dir = data_dir / "inputs"
        outputs_dir = data_dir / "outputs"
        config_dir = data_dir / "config" / "comfy" / "pipelines"

        for d in [inputs_dir, outputs_dir, config_dir]:
            d.mkdir(parents=True, exist_ok=True)

        yield data_dir, inputs_dir, outputs_dir, config_dir


@pytest.fixture
def mock_comfy_client():
    """Create a mock ComfyUI client."""
    client = Mock(spec=ComfyUIClient)
    client.upload_image = Mock(return_value="uploaded_image.jpg")
    client.queue_prompt = Mock(return_value="test-prompt-123")
    client.wait_for_completion = Mock(
        return_value={"status": {"status_str": "success"}}
    )
    client.get_output_images = Mock(return_value=["output1.jpg"])
    client.download_image = Mock()
    return client


@pytest.fixture
def mock_pipeline_loader(temp_dirs):
    """Create a mock pipeline loader."""
    _, _, _, config_dir = temp_dirs
    loader = Mock(spec=PipelineLoader)
    loader.prepare_workflow = Mock(return_value={"1": {"class_type": "TestNode"}})
    return loader


@pytest.fixture
def image_tool(temp_dirs, mock_comfy_client, mock_pipeline_loader):
    """Create an ImagePipelineTool instance."""
    data_dir, _, _, _ = temp_dirs
    return ImagePipelineTool(
        data_dir=data_dir,
        comfy_client=mock_comfy_client,
        pipeline_loader=mock_pipeline_loader,
    )


def test_select_pipeline_cleanup(image_tool):
    """Test pipeline selection for cleanup purpose."""
    pipeline = image_tool._select_pipeline("clean up car photos")
    assert pipeline == "photo_cleanup_v1"


def test_select_pipeline_enhance(image_tool):
    """Test pipeline selection for enhancement purpose."""
    pipeline = image_tool._select_pipeline("enhance product images")
    assert pipeline == "photo_cleanup_v1"


def test_extract_style_hints_premium(image_tool):
    """Test extracting premium style hint."""
    hints = image_tool._extract_style_hints("make it look premium")
    assert "premium" in hints


def test_extract_style_hints_multiple(image_tool):
    """Test extracting multiple style hints."""
    hints = image_tool._extract_style_hints("bright and vibrant")
    assert "bright" in hints
    assert "vibrant" in hints


def test_extract_style_hints_none(image_tool):
    """Test extracting style hints when none provided."""
    hints = image_tool._extract_style_hints(None)
    assert hints == []


def test_execute_single_image(image_tool, temp_dirs, mock_comfy_client):
    """Test executing pipeline on a single image."""
    data_dir, inputs_dir, _, _ = temp_dirs

    # Create test image
    test_image = inputs_dir / "test.jpg"
    test_image.write_bytes(b"fake image data")

    result = image_tool.execute(
        purpose="clean up photo",
        input_paths=["test.jpg"],
        job_id="test-job",
    )

    assert result["tool"] == "IMAGE_PIPELINE"
    assert result["input_count"] == 1
    assert mock_comfy_client.upload_image.called
    assert mock_comfy_client.queue_prompt.called


def test_execute_multiple_images(image_tool, temp_dirs, mock_comfy_client):
    """Test executing pipeline on multiple images."""
    data_dir, inputs_dir, _, _ = temp_dirs

    # Create test images
    for i in range(3):
        test_image = inputs_dir / f"test{i}.jpg"
        test_image.write_bytes(b"fake image data")

    result = image_tool.execute(
        purpose="enhance photos",
        input_paths=["test0.jpg", "test1.jpg", "test2.jpg"],
    )

    assert result["input_count"] == 3
    assert mock_comfy_client.upload_image.call_count == 3


def test_execute_nonexistent_image(image_tool):
    """Test executing pipeline with non-existent image."""
    result = image_tool.execute(
        purpose="clean up",
        input_paths=["nonexistent.jpg"],
    )

    assert result["status"] in ["partial", "failed"]
    assert len(result["errors"]) > 0


def test_inject_image_input(image_tool):
    """Test injecting image input into workflow."""
    workflow = {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": "IMAGE_INPUT"},
        }
    }

    result = image_tool._inject_image_input(workflow, "test_image.jpg")

    assert result["1"]["inputs"]["image"] == "test_image.jpg"

