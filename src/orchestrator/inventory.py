"""
File inventory scanning and classification.

Scans the inputs/ directory and classifies files by type,
generating an inventory JSON file.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# File type mappings
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".bmp", ".gif"}
DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".html", ".rtf", ".odt"}
DATA_EXTENSIONS = {".csv", ".json", ".xml", ".yaml", ".yml"}
AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}  # Future support


class InventoryItem:
    """Represents a single file in the inventory."""

    def __init__(
        self,
        path: str,
        file_type: str,
        size_bytes: int,
        relative_path: Optional[str] = None,
    ):
        self.path = path
        self.file_type = file_type
        self.size_bytes = size_bytes
        self.relative_path = relative_path or path

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "path": self.relative_path,
            "type": self.file_type,
            "size_bytes": self.size_bytes,
            "full_path": self.path,
        }


class InventoryScanner:
    """Scans and classifies files in the inputs directory."""

    def __init__(self, inputs_dir: Path, runtime_dir: Path):
        """Initialize scanner with directory paths."""
        self.inputs_dir = Path(inputs_dir)
        self.runtime_dir = Path(runtime_dir)
        self.inventory_file = self.runtime_dir / "inputs-inventory.json"

        # Ensure directories exist
        self.inputs_dir.mkdir(parents=True, exist_ok=True)
        self.runtime_dir.mkdir(parents=True, exist_ok=True)

    def _classify_file(self, file_path: Path) -> str:
        """Classify a file by its extension."""
        ext = file_path.suffix.lower()

        if ext in IMAGE_EXTENSIONS:
            return "image"
        elif ext in DOCUMENT_EXTENSIONS:
            return "document"
        elif ext in DATA_EXTENSIONS:
            return "data"
        elif ext in AUDIO_EXTENSIONS:
            return "audio"
        else:
            return "unknown"

    def _scan_directory(self, directory: Path, base_path: Path) -> List[InventoryItem]:
        """Recursively scan a directory and return inventory items."""
        items = []

        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return items

        try:
            for item_path in directory.rglob("*"):
                if item_path.is_file():
                    try:
                        size = item_path.stat().st_size
                        file_type = self._classify_file(item_path)
                        relative_path = str(item_path.relative_to(base_path))

                        items.append(
                            InventoryItem(
                                path=str(item_path),
                                file_type=file_type,
                                size_bytes=size,
                                relative_path=relative_path,
                            )
                        )
                    except (OSError, PermissionError) as e:
                        logger.warning(f"Error accessing file {item_path}: {e}")
                        continue

        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")

        return items

    def scan(self) -> Dict:
        """Scan inputs directory and generate inventory."""
        logger.info(f"Scanning inputs directory: {self.inputs_dir}")

        items = self._scan_directory(self.inputs_dir, self.inputs_dir)

        # Group by type for summary
        type_counts = {}
        total_size = 0

        for item in items:
            file_type = item.file_type
            type_counts[file_type] = type_counts.get(file_type, 0) + 1
            total_size += item.size_bytes

        inventory = {
            "scanned_at": datetime.utcnow().isoformat() + "Z",
            "inputs_dir": str(self.inputs_dir),
            "total_files": len(items),
            "total_size_bytes": total_size,
            "type_counts": type_counts,
            "items": [item.to_dict() for item in items],
        }

        # Save to runtime directory
        try:
            with open(self.inventory_file, "w") as f:
                json.dump(inventory, f, indent=2)
            logger.info(f"Inventory saved to {self.inventory_file}")
        except Exception as e:
            logger.error(f"Error saving inventory: {e}")

        return inventory

    def load_inventory(self) -> Optional[Dict]:
        """Load the last saved inventory."""
        if not self.inventory_file.exists():
            return None

        try:
            with open(self.inventory_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading inventory: {e}")
            return None

