"""
Tests for manifest management functionality.
"""

import json
import tempfile
from pathlib import Path

import pytest

from src.orchestrator.manifest import ManifestManager


@pytest.fixture
def temp_outputs_dir():
    """Create a temporary outputs directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        outputs_dir = Path(tmpdir) / "outputs"
        outputs_dir.mkdir()
        yield outputs_dir


@pytest.fixture
def manifest_manager(temp_outputs_dir):
    """Create a ManifestManager instance."""
    return ManifestManager(temp_outputs_dir)


def test_create_manifest(manifest_manager):
    """Test creating a new manifest."""
    job_id = "test-job-123"
    intent = "Test intent"
    inventory = {
        "total_files": 5,
        "type_counts": {"image": 3, "document": 2},
    }

    manifest = manifest_manager.create_manifest(
        job_id=job_id,
        intent=intent,
        inventory=inventory,
        steps=[],
    )

    assert manifest["job_id"] == job_id
    assert manifest["intent"] == intent
    assert manifest["status"] == "pending"
    assert manifest["inventory"]["total_files"] == 5
    assert "created_at" in manifest
    assert "updated_at" in manifest


def test_manifest_saved_to_file(manifest_manager, temp_outputs_dir):
    """Test that manifest is saved to file."""
    job_id = "test-job-456"
    manifest = manifest_manager.create_manifest(
        job_id=job_id,
        intent="Test",
        inventory={"total_files": 0, "type_counts": {}},
    )

    manifest_file = temp_outputs_dir / job_id / "manifest.json"
    assert manifest_file.exists()

    with open(manifest_file) as f:
        saved_manifest = json.load(f)

    assert saved_manifest["job_id"] == job_id


def test_load_manifest(manifest_manager):
    """Test loading a manifest."""
    job_id = "test-job-789"
    manifest_manager.create_manifest(
        job_id=job_id,
        intent="Test intent",
        inventory={"total_files": 0, "type_counts": {}},
    )

    loaded = manifest_manager.load_manifest(job_id)
    assert loaded is not None
    assert loaded["job_id"] == job_id
    assert loaded["intent"] == "Test intent"


def test_load_nonexistent_manifest(manifest_manager):
    """Test loading a manifest that doesn't exist."""
    loaded = manifest_manager.load_manifest("nonexistent-job")
    assert loaded is None


def test_update_status(manifest_manager):
    """Test updating job status."""
    job_id = "test-job-status"
    manifest_manager.create_manifest(
        job_id=job_id,
        intent="Test",
        inventory={"total_files": 0, "type_counts": {}},
    )

    manifest_manager.update_status(job_id, "running")

    loaded = manifest_manager.load_manifest(job_id)
    assert loaded["status"] == "running"


def test_add_step(manifest_manager):
    """Test adding a step to manifest."""
    job_id = "test-job-steps"
    manifest_manager.create_manifest(
        job_id=job_id,
        intent="Test",
        inventory={"total_files": 0, "type_counts": {}},
    )

    step = manifest_manager.add_step(
        job_id=job_id,
        step_name="test_step",
        step_type="image_pipeline",
        inputs=["input1.jpg"],
        status="pending",
    )

    assert step["name"] == "test_step"
    assert step["type"] == "image_pipeline"
    assert step["status"] == "pending"
    assert step["inputs"] == ["input1.jpg"]

    loaded = manifest_manager.load_manifest(job_id)
    assert len(loaded["steps"]) == 1


def test_update_step(manifest_manager):
    """Test updating a step."""
    job_id = "test-job-update-step"
    manifest_manager.create_manifest(
        job_id=job_id,
        intent="Test",
        inventory={"total_files": 0, "type_counts": {}},
    )

    manifest_manager.add_step(
        job_id=job_id,
        step_name="test_step",
        step_type="test",
        inputs=[],
    )

    manifest_manager.update_step(
        job_id=job_id,
        step_index=0,
        status="running",
    )

    loaded = manifest_manager.load_manifest(job_id)
    step = loaded["steps"][0]
    assert step["status"] == "running"
    assert step["started_at"] is not None


def test_update_step_completed(manifest_manager):
    """Test updating step to completed status."""
    job_id = "test-job-complete"
    manifest_manager.create_manifest(
        job_id=job_id,
        intent="Test",
        inventory={"total_files": 0, "type_counts": {}},
    )

    manifest_manager.add_step(
        job_id=job_id,
        step_name="test_step",
        step_type="test",
        inputs=[],
    )

    manifest_manager.update_step(
        job_id=job_id,
        step_index=0,
        status="completed",
        outputs=["output1.jpg"],
    )

    loaded = manifest_manager.load_manifest(job_id)
    step = loaded["steps"][0]
    assert step["status"] == "completed"
    assert step["completed_at"] is not None
    assert "output1.jpg" in step["outputs"]


def test_add_output(manifest_manager):
    """Test adding output to manifest."""
    job_id = "test-job-output"
    manifest_manager.create_manifest(
        job_id=job_id,
        intent="Test",
        inventory={"total_files": 0, "type_counts": {}},
    )

    manifest_manager.add_output(job_id, "images", "output/image1.jpg")

    loaded = manifest_manager.load_manifest(job_id)
    assert "image1.jpg" in loaded["outputs"]["images"]


def test_add_output_multiple(manifest_manager):
    """Test adding multiple outputs."""
    job_id = "test-job-multi-output"
    manifest_manager.create_manifest(
        job_id=job_id,
        intent="Test",
        inventory={"total_files": 0, "type_counts": {}},
    )

    manifest_manager.add_output(job_id, "images", "output/image1.jpg")
    manifest_manager.add_output(job_id, "images", "output/image2.jpg")
    manifest_manager.add_output(job_id, "docs", "output/report.md")

    loaded = manifest_manager.load_manifest(job_id)
    assert len(loaded["outputs"]["images"]) == 2
    assert len(loaded["outputs"]["docs"]) == 1

