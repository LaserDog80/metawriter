"""Handler registry — maps file extensions to in-place stampers."""

from pathlib import Path

from ..stamper import UnsupportedFormatError
from .jpeg import JpegStamper
from .png import PngStamper
from .tiff import TiffStamper
from .video import VideoStamper
from .webp import WebpStamper

_HANDLERS: dict[str, object] = {
    ".png": PngStamper(),
    ".jpg": JpegStamper(),
    ".jpeg": JpegStamper(),
    ".tiff": TiffStamper(),
    ".tif": TiffStamper(),
    ".webp": WebpStamper(),
    ".mp4": VideoStamper(),
    ".mov": VideoStamper(),
    ".mkv": VideoStamper(),
}


def get_handler(path: Path):
    """Return the appropriate stamper for a file.

    Args:
        path: Path to the media file.

    Returns:
        A handler instance with a stamp() method.

    Raises:
        UnsupportedFormatError: If the extension is not supported.
    """
    ext = path.suffix.lower()
    handler = _HANDLERS.get(ext)
    if handler is None:
        raise UnsupportedFormatError(ext)
    return handler
