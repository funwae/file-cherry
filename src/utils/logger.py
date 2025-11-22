"""
Structured logging utility for FileCherry.

Provides JSON-line logging with rotation and structured fields.
"""

import json
import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class StructuredFormatter(logging.Formatter):
    """Formatter that outputs JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "component": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields from record
        if hasattr(record, "job_id"):
            log_data["job_id"] = record.job_id
        if hasattr(record, "step_id"):
            log_data["step_id"] = record.step_id
        if hasattr(record, "file_path"):
            log_data["file_path"] = record.file_path
        if hasattr(record, "error_code"):
            log_data["error_code"] = record.error_code

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logger(
    name: str,
    log_dir: Path,
    log_file: str,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Set up a structured logger with file rotation.

    Args:
        name: Logger name
        log_dir: Directory for log files
        log_file: Log filename
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        level: Logging level

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / log_file

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(StructuredFormatter())
    logger.addHandler(file_handler)

    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(StructuredFormatter())
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str, data_dir: Optional[Path] = None) -> logging.Logger:
    """
    Get a logger instance for a component.

    Args:
        name: Component name (e.g., 'orchestrator', 'doc-service')
        data_dir: Data directory (defaults to FILECHERRY_DATA_DIR env var)

    Returns:
        Logger instance
    """
    if data_dir is None:
        data_dir = Path(os.getenv("FILECHERRY_DATA_DIR", "/data"))

    log_dir = data_dir / "logs"
    log_file = f"{name}.log"

    return setup_logger(name, log_dir, log_file)


def log_job_event(
    logger: logging.Logger,
    level: int,
    message: str,
    job_id: Optional[str] = None,
    step_id: Optional[str] = None,
    **kwargs,
):
    """
    Log a job-related event with structured fields.

    Args:
        logger: Logger instance
        level: Log level
        message: Log message
        job_id: Optional job ID
        step_id: Optional step ID
        **kwargs: Additional fields to include
    """
    extra = {}
    if job_id:
        extra["job_id"] = job_id
    if step_id:
        extra["step_id"] = step_id
    extra.update(kwargs)

    logger.log(level, message, extra=extra)

