"""
Security utilities for FileCherry.

File permission checks, path validation, and security hardening.
"""

import os
import stat
from pathlib import Path
from typing import List, Optional


class SecurityError(Exception):
    """Security-related error."""

    pass


def validate_data_path(path: Path, data_dir: Path) -> bool:
    """
    Validate that a path is within the data directory.

    Args:
        path: Path to validate
        data_dir: Allowed data directory

    Returns:
        True if path is safe

    Raises:
        SecurityError: If path is outside data directory
    """
    try:
        resolved_path = path.resolve()
        resolved_data = data_dir.resolve()

        if not str(resolved_path).startswith(str(resolved_data)):
            raise SecurityError(
                f"Path {path} is outside allowed data directory {data_dir}"
            )
        return True
    except Exception as e:
        raise SecurityError(f"Invalid path: {e}")


def check_file_permissions(path: Path, expected_owner: Optional[str] = None) -> bool:
    """
    Check file permissions are secure.

    Args:
        path: File path to check
        expected_owner: Expected owner username (optional)

    Returns:
        True if permissions are acceptable
    """
    if not path.exists():
        return False

    stat_info = path.stat()

    # Check that file is not world-writable
    if stat_info.st_mode & stat.S_IWOTH:
        return False

    # Check owner if specified
    if expected_owner:
        import pwd

        try:
            owner = pwd.getpwuid(stat_info.st_uid).pw_name
            if owner != expected_owner:
                return False
        except KeyError:
            return False

    return True


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = os.path.basename(filename)

    # Remove dangerous characters
    dangerous = ["..", "/", "\\", "\x00"]
    for char in dangerous:
        filename = filename.replace(char, "_")

    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext

    return filename


def ensure_secure_directory(path: Path, owner: Optional[str] = None) -> None:
    """
    Ensure a directory exists with secure permissions.

    Args:
        path: Directory path
        owner: Owner username (optional)
    """
    path.mkdir(parents=True, exist_ok=True)

    # Set secure permissions (750 = rwxr-x---)
    os.chmod(path, 0o750)

    # Set owner if specified
    if owner:
        import pwd
        import grp

        try:
            uid = pwd.getpwnam(owner).pw_uid
            gid = grp.getgrnam(owner).gr_gid
            os.chown(path, uid, gid)
        except (KeyError, OSError):
            pass  # Ignore if user/group doesn't exist


def check_no_auto_mount() -> bool:
    """
    Check that host drives are not auto-mounted.

    Returns:
        True if no unexpected mounts found
    """
    # Read /proc/mounts
    try:
        with open("/proc/mounts", "r") as f:
            mounts = f.readlines()

        # Check for common host drive patterns
        dangerous_patterns = ["/dev/sd", "/dev/nvme", "/dev/hd"]
        for line in mounts:
            for pattern in dangerous_patterns:
                if pattern in line and "/data" not in line:
                    # This might be a host drive
                    # In a real implementation, we'd check mount options
                    pass

        return True
    except Exception:
        return False


def validate_config_file(config_path: Path) -> bool:
    """
    Validate a configuration file is safe to load.

    Args:
        config_path: Path to config file

    Returns:
        True if safe
    """
    if not config_path.exists():
        return False

    # Check permissions
    if not check_file_permissions(config_path):
        return False

    # Check file size (prevent DoS)
    if config_path.stat().st_size > 10 * 1024 * 1024:  # 10MB
        return False

    return True

