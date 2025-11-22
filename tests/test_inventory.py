"""
Tests for inventory scanning functionality.
"""

import json
import tempfile
from pathlib import Path

import pytest

from src.orchestrator.inventory import InventoryScanner, InventoryItem


@pytest.fixture
def temp_inputs_dir():
    """Create a temporary inputs directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        inputs_dir = Path(tmpdir) / "inputs"
        inputs_dir.mkdir()
        yield inputs_dir


@pytest.fixture
def temp_runtime_dir():
    """Create a temporary runtime directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runtime_dir = Path(tmpdir) / "runtime"
        runtime_dir.mkdir()
        yield runtime_dir


@pytest.fixture
def scanner(temp_inputs_dir, temp_runtime_dir):
    """Create an InventoryScanner instance."""
    return InventoryScanner(temp_inputs_dir, temp_runtime_dir)


def test_classify_image_file(scanner):
    """Test classification of image files."""
    assert scanner._classify_file(Path("test.jpg")) == "image"
    assert scanner._classify_file(Path("test.png")) == "image"
    assert scanner._classify_file(Path("test.webp")) == "image"


def test_classify_document_file(scanner):
    """Test classification of document files."""
    assert scanner._classify_file(Path("test.pdf")) == "document"
    assert scanner._classify_file(Path("test.docx")) == "document"
    assert scanner._classify_file(Path("test.txt")) == "document"
    assert scanner._classify_file(Path("test.md")) == "document"


def test_classify_data_file(scanner):
    """Test classification of data files."""
    assert scanner._classify_file(Path("test.csv")) == "data"
    assert scanner._classify_file(Path("test.json")) == "data"


def test_classify_unknown_file(scanner):
    """Test classification of unknown file types."""
    assert scanner._classify_file(Path("test.xyz")) == "unknown"


def test_scan_empty_directory(scanner):
    """Test scanning an empty directory."""
    inventory = scanner.scan()
    assert inventory["total_files"] == 0
    assert inventory["items"] == []
    assert inventory["type_counts"] == {}


def test_scan_with_files(scanner, temp_inputs_dir):
    """Test scanning a directory with files."""
    # Create test files
    (temp_inputs_dir / "image1.jpg").write_bytes(b"fake image data")
    (temp_inputs_dir / "doc1.pdf").write_bytes(b"fake pdf data")
    (temp_inputs_dir / "data1.csv").write_bytes(b"fake csv data")

    inventory = scanner.scan()

    assert inventory["total_files"] == 3
    assert len(inventory["items"]) == 3
    assert inventory["type_counts"]["image"] == 1
    assert inventory["type_counts"]["document"] == 1
    assert inventory["type_counts"]["data"] == 1

    # Check that items have correct structure
    for item in inventory["items"]:
        assert "path" in item
        assert "type" in item
        assert "size_bytes" in item
        assert "full_path" in item


def test_scan_recursive(scanner, temp_inputs_dir):
    """Test scanning nested directories."""
    # Create nested structure
    subdir = temp_inputs_dir / "subdir"
    subdir.mkdir()
    (subdir / "nested.jpg").write_bytes(b"nested image")

    inventory = scanner.scan()

    assert inventory["total_files"] == 1
    assert any("subdir/nested.jpg" in item["path"] for item in inventory["items"])


def test_inventory_saved_to_file(scanner, temp_inputs_dir, temp_runtime_dir):
    """Test that inventory is saved to file."""
    (temp_inputs_dir / "test.jpg").write_bytes(b"test")

    scanner.scan()

    inventory_file = temp_runtime_dir / "inputs-inventory.json"
    assert inventory_file.exists()

    with open(inventory_file) as f:
        saved_inventory = json.load(f)

    assert saved_inventory["total_files"] == 1


def test_load_inventory(scanner, temp_inputs_dir, temp_runtime_dir):
    """Test loading a saved inventory."""
    # Create and save inventory
    (temp_inputs_dir / "test.jpg").write_bytes(b"test")
    scanner.scan()

    # Load it back
    loaded = scanner.load_inventory()
    assert loaded is not None
    assert loaded["total_files"] == 1


def test_load_nonexistent_inventory(scanner):
    """Test loading inventory when file doesn't exist."""
    loaded = scanner.load_inventory()
    assert loaded is None

