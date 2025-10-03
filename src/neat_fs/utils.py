"""Utility functions for the neat_fs package."""


import logging


def setup_logging(verbose: bool = False) -> None:
    """Configure logging with appropriate level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level, format='%(message)s', handlers=[logging.StreamHandler()]
    )



def parse_file_mode(st_mode: int) -> tuple[str, str]:
    """
    Parse st_mode to extract file type and permissions.

    Args:
        st_mode: The st_mode value from os.stat()

    Returns:
        tuple: (file_type, permissions) where:
            - file_type: 'file', 'directory', 'symlink', etc.
            - permissions: '644', '755', etc.
    """
    # Extract file type
    file_type_mask = 0o170000
    file_type_bits = st_mode & file_type_mask

    if file_type_bits == 0o040000:
        file_type = "directory"
    elif file_type_bits == 0o100000:
        file_type = "file"
    elif file_type_bits == 0o120000:
        file_type = "symlink"
    elif file_type_bits == 0o060000:
        file_type = "block_device"
    elif file_type_bits == 0o020000:
        file_type = "char_device"
    elif file_type_bits == 0o010000:
        file_type = "fifo"
    elif file_type_bits == 0o140000:
        file_type = "socket"
    else:
        file_type = "unknown"

    # Extract permissions (frist 12 bits)
    permissions = oct(st_mode & 0o7777)[2:]

    return file_type, permissions
