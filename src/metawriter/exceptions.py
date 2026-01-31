"""Custom exception hierarchy for MetaWriter."""


class MetaWriterError(Exception):
    """Base exception for all MetaWriter errors."""


class UnsupportedFormatError(MetaWriterError):
    """Raised when a file format is not supported by MetaWriter."""

    def __init__(self, extension: str) -> None:
        self.extension = extension
        super().__init__(
            f"Unsupported file format: '{extension}'. "
            f"Supported formats: .png, .jpg, .jpeg, .tiff, .tif, .webp, "
            f".mp4, .mov, .mkv"
        )


class FormatMismatchError(MetaWriterError):
    """Raised when a file's extension doesn't match its actual content."""

    def __init__(self, path: str, expected: str, actual: str) -> None:
        self.path = path
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"Format mismatch for '{path}': extension suggests {expected}, "
            f"but content is {actual}"
        )


class MetadataIntegrityError(MetaWriterError):
    """Raised when post-write verification detects missing metadata."""

    def __init__(self, missing_keys: list[str]) -> None:
        self.missing_keys = missing_keys
        super().__init__(
            f"Metadata integrity check failed. "
            f"Missing keys in output: {missing_keys}"
        )


class VideoToolMissingError(MetaWriterError):
    """Raised when ffmpeg/ffprobe is not found on the system."""

    def __init__(self, tool: str) -> None:
        self.tool = tool
        super().__init__(
            f"'{tool}' not found on system PATH. "
            f"Video metadata support requires ffmpeg and ffprobe. "
            f"Install from https://ffmpeg.org/ or via your package manager."
        )
