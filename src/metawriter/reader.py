"""Read-only metadata extraction from media files."""

from pathlib import Path

from .formats import get_handler
from .models import MWRITE_SUFFIX


def read_metadata(path: str | Path, *, only_mwrite: bool = False) -> dict[str, str]:
    """Read all metadata from a media file.

    Args:
        path: Path to the media file.
        only_mwrite: If True, return only entries whose keys end with
            the ``_mwrite`` suffix.

    Returns:
        Dict mapping metadata keys to their string values.

    Raises:
        FileNotFoundError: If the file does not exist.
        UnsupportedFormatError: If the format is not supported.
        FormatMismatchError: If extension/content mismatch detected.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {path}")

    handler = get_handler(path)
    metadata = handler.read_metadata(path)

    if only_mwrite:
        return {k: v for k, v in metadata.items() if k.endswith(MWRITE_SUFFIX)}

    return metadata
