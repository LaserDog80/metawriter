"""Core MetadataWriter — append metadata to media files (new-copy output)."""

from pathlib import Path

from .exceptions import MetadataIntegrityError
from .formats import get_handler
from .formats.base import BaseFormatHandler
from .models import entries_to_dict, validate_entries


def _default_output_path(source: Path) -> Path:
    """Generate the default output path: ``<name>_mwrite.<ext>``."""
    return source.with_name(f"{source.stem}_mwrite{source.suffix}")


def append_metadata(
    source: str | Path,
    entries: dict[str, str],
    *,
    output_path: str | Path | None = None,
) -> str:
    """Append metadata entries to a media file, producing a new copy.

    The original file is never modified. A new file is created with all
    existing metadata carried forward plus the new entries appended.

    Args:
        source: Path to the original media file.
        entries: Dict of metadata field names to string values. The
            ``_mwrite`` suffix is appended automatically to each key.
        output_path: Optional custom output path. If omitted, defaults
            to ``<name>_mwrite.<ext>`` alongside the source.

    Returns:
        The string path of the newly created output file.

    Raises:
        FileNotFoundError: If the source file or output directory is missing.
        FileExistsError: If the output path already exists.
        UnsupportedFormatError: If the format is not supported.
        FormatMismatchError: If extension/content don't match.
        MetadataIntegrityError: If post-write verification fails.
        ValueError: If a key is empty.
        TypeError: If a key or value is not a string.
    """
    source = Path(source)
    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {source}")

    out = Path(output_path) if output_path else _default_output_path(source)

    if not out.parent.exists():
        raise FileNotFoundError(
            f"Output directory does not exist: {out.parent}"
        )
    if out.exists():
        raise FileExistsError(
            f"Output file already exists: {out}. "
            f"Delete it first or choose a different path."
        )

    validated = validate_entries(entries)
    metadata_dict = entries_to_dict(validated)

    handler = get_handler(source)

    existing_metadata = handler.read_metadata(source)

    handler.write_metadata(source, out, metadata_dict)

    _verify_integrity(out, existing_metadata, handler)

    return str(out)


def _verify_integrity(
    output_path: Path,
    original_metadata: dict[str, str],
    handler: BaseFormatHandler,
) -> None:
    """Re-read the output file and verify pre-existing metadata survived.

    Args:
        output_path: Path to the newly written file.
        original_metadata: Snapshot of metadata from the source.
        handler: The format handler used for the write.

    Raises:
        MetadataIntegrityError: If any original keys are missing.
    """
    output_metadata = handler.read_metadata(output_path)
    missing = [
        key for key in original_metadata
        if key not in output_metadata
    ]
    if missing:
        raise MetadataIntegrityError(missing)
