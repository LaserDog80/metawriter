"""Nametag — stamp old filenames into file metadata in-place."""

from .stamper import (
    METADATA_KEY,
    UnsupportedFormatError,
    VideoToolMissingError,
    stamp_previous_name,
)

__all__ = [
    "stamp_previous_name",
    "METADATA_KEY",
    "UnsupportedFormatError",
    "VideoToolMissingError",
]
__version__ = "0.1.0"
