"""
Utility modules for FileCherry.

Provides logging, security, and error recovery utilities.
"""

from .logger import get_logger, log_job_event, setup_logger
from .security import (
    SecurityError,
    check_file_permissions,
    check_no_auto_mount,
    ensure_secure_directory,
    sanitize_filename,
    validate_config_file,
    validate_data_path,
)
from .error_recovery import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    idempotent_operation,
    retry_with_backoff,
)

__all__ = [
    # Logger
    "get_logger",
    "log_job_event",
    "setup_logger",
    # Security
    "SecurityError",
    "check_file_permissions",
    "check_no_auto_mount",
    "ensure_secure_directory",
    "sanitize_filename",
    "validate_config_file",
    "validate_data_path",
    # Error recovery
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "idempotent_operation",
    "retry_with_backoff",
]

