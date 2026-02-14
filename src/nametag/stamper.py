"""Core stamper logic — detect format, dispatch to handler, write in-place."""

from pathlib import Path

METADATA_KEY = "previous_name_mwrite"


class UnsupportedFormatError(Exception):
    """File format not supported by Nametag."""

    def __init__(self, extension: str) -> None:
        self.extension = extension
        super().__init__(
            f"Unsupported format: '{extension}'. "
            f"Supported: .jpg, .jpeg, .png, .tiff, .tif, .webp, .mp4, .mov, .mkv"
        )


class VideoToolMissingError(Exception):
    """ffmpeg/ffprobe not found on PATH."""

    def __init__(self, tool: str) -> None:
        self.tool = tool
        super().__init__(
            f"'{tool}' not found. Video support requires ffmpeg. "
            f"Install from https://ffmpeg.org/"
        )


def stamp_previous_name(file_path: str | Path, old_name: str) -> None:
    """Stamp the previous filename into a file's metadata in-place.

    Args:
        file_path: Path to the file to modify.
        old_name: The old filename (name only, not full path) to record.

    Raises:
        FileNotFoundError: If file_path does not exist.
        ValueError: If old_name is empty or whitespace-only.
        TypeError: If old_name is not a string.
        UnsupportedFormatError: If the file format is not supported.
        VideoToolMissingError: If ffmpeg is needed but not installed.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    old_name = _validate_old_name(old_name)

    from .handlers import get_handler

    handler = get_handler(file_path)
    handler.stamp(file_path, METADATA_KEY, old_name)


def _validate_old_name(old_name: str) -> str:
    """Validate and return the stripped old_name.

    Raises:
        TypeError: If old_name is not a string.
        ValueError: If old_name is empty or whitespace-only.
    """
    if not isinstance(old_name, str):
        raise TypeError(
            f"old_name must be a string, got {type(old_name).__name__}"
        )
    stripped = old_name.strip()
    if not stripped:
        raise ValueError("old_name must not be empty or whitespace-only")
    return stripped
