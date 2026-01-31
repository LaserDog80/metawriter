"""Format registry — maps file extensions to their handlers."""

from pathlib import Path

from ..exceptions import FormatMismatchError, UnsupportedFormatError
from .base import BaseFormatHandler
from .jpeg import JpegHandler
from .png import PngHandler
from .tiff import TiffHandler
from .video import VideoHandler
from .webp import WebpHandler

# Canonical extension → handler mapping.
_HANDLERS: dict[str, BaseFormatHandler] = {
    ".png": PngHandler(),
    ".jpg": JpegHandler(),
    ".jpeg": JpegHandler(),
    ".tiff": TiffHandler(),
    ".tif": TiffHandler(),
    ".webp": WebpHandler(),
    ".mp4": VideoHandler(),
    ".mov": VideoHandler(),
    ".mkv": VideoHandler(),
}

# Extension → expected magic-byte format name.
_EXPECTED_FORMAT: dict[str, str] = {
    ".png": "png",
    ".jpg": "jpeg",
    ".jpeg": "jpeg",
    ".tiff": "tiff",
    ".tif": "tiff",
    ".webp": "webp",
    ".mp4": "mp4",
    ".mov": "mov",
    ".mkv": "mkv",
}


def get_handler(path: Path) -> BaseFormatHandler:
    """Return the appropriate handler for a file, with magic-byte validation.

    Args:
        path: Path to the media file.

    Returns:
        A format handler instance.

    Raises:
        UnsupportedFormatError: If the extension is not supported.
        FormatMismatchError: If magic bytes don't match the extension.
    """
    ext = path.suffix.lower()
    handler = _HANDLERS.get(ext)
    if handler is None:
        raise UnsupportedFormatError(ext)

    # Validate magic bytes (mp4 and mov share ftyp container, treat as compatible)
    detected = BaseFormatHandler.detect_magic(path)
    expected = _EXPECTED_FORMAT.get(ext)
    if detected is not None and expected is not None and detected != expected:
        compatible = {frozenset(("mp4", "mov"))}
        pair = frozenset((detected, expected))
        if pair not in compatible:
            raise FormatMismatchError(str(path), expected, detected)

    return handler
