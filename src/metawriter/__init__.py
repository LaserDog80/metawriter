"""MetaWriter — preserve file identity through renames.

Stamps filenames, download timestamps, and AI-provenance metadata into
media files in-place so the information survives renames.

Public API:
    tag_file(file_path, ...) -> dict[str, str]
    tag_files(paths, ...) -> list[Path]
    read_metadata(path, *, only_mwrite=False) -> dict[str, str]
    scan_paths(paths, *, recursive=False) -> list[Path]
"""

from .engine import tag_file, tag_files
from .reader import read_metadata
from .scanner import scan_paths

# Keep append_metadata available for backward compatibility / existing tests
from .writer import append_metadata

__all__ = ["tag_file", "tag_files", "read_metadata", "scan_paths", "append_metadata"]
__version__ = "0.2.0"
