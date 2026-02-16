"""Abstract base class for format-specific metadata handlers."""

from abc import ABC, abstractmethod
from pathlib import Path


class BaseFormatHandler(ABC):
    """Interface that every format handler must implement."""

    @abstractmethod
    def read_metadata(self, path: Path) -> dict[str, str]:
        """Read all metadata from a file.

        Args:
            path: Path to the file.

        Returns:
            Dict mapping metadata keys to their string values.
        """

    @abstractmethod
    def write_metadata(
        self,
        source_path: Path,
        output_path: Path,
        metadata: dict[str, str],
    ) -> None:
        """Copy source to output with merged metadata.

        The implementation must:
        1. Read all existing metadata from source_path.
        2. Merge in the new metadata entries (append, never replace).
        3. Write the result to output_path.

        Args:
            source_path: Original file (must not be modified).
            output_path: Destination for the new copy.
            metadata: New key-value entries to append.
        """

    def write_metadata_inplace(
        self,
        path: Path,
        metadata: dict[str, str],
    ) -> None:
        """Write metadata into a file in-place.

        Uses a temp file and atomic replace to avoid corruption.

        Args:
            path: File to modify in-place.
            metadata: Key-value entries to write.
        """
        tmp = path.with_name(path.stem + "_mwrite_tmp" + path.suffix)
        try:
            self.write_metadata(path, tmp, metadata)
            tmp.replace(path)
        except Exception:
            if tmp.exists():
                tmp.unlink()
            raise

    @staticmethod
    def detect_magic(path: Path) -> str | None:
        """Return the detected format name based on file magic bytes.

        Returns:
            A lowercase format string (e.g. 'png', 'jpeg', 'tiff', 'webp',
            'mp4', 'mkv') or None if unrecognised.
        """
        header = path.read_bytes()[:32]

        if header[:8] == b"\x89PNG\r\n\x1a\n":
            return "png"
        if header[:3] == b"\xff\xd8\xff":
            return "jpeg"
        if header[:4] in (b"II*\x00", b"MM\x00*"):
            return "tiff"
        if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
            return "webp"
        if header[4:8] == b"ftyp":
            # MP4 / MOV — distinguish by ftyp brand
            brand = header[8:12]
            if brand in (b"qt  ", b"MSNV"):
                return "mov"
            return "mp4"
        if header[:4] == b"\x1a\x45\xdf\xa3":
            return "mkv"

        return None
