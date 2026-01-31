"""MetaWriter — append-only AI-provenance metadata for media files.

Public API:
    append_metadata(source, entries, *, output_path=None) -> str
    read_metadata(path, *, only_mwrite=False) -> dict[str, str]
"""

from .reader import read_metadata
from .writer import append_metadata

__all__ = ["append_metadata", "read_metadata"]
__version__ = "0.1.0"
